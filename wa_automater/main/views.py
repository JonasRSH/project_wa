from django.shortcuts import render, redirect
import pandas as pd
import os
import re
from django.conf import settings
import sys
import pathlib
from pypdf import PdfReader
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR / 'Python_Back_End' / 'loading_list_check'))
sys.path.append(str(BASE_DIR / 'Python_Back_End' / 't1_reader'))
from CustomsList import Shipment
from t1_reader import data_filter as t1_data_filter
from .models import Abfahrt, Zollamt, Shipment as ShipmentModel, Colli, TransitDocument
from django.db.models import Sum
from django.http import FileResponse, Http404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
import base64
from io import BytesIO


def _is_pdf(file_obj):
    """Prüft die PDF-Magic-Bytes (%PDF)."""
    header = file_obj.read(5)
    file_obj.seek(0)
    return header.startswith(b'%PDF')


def _validate_abmeldeliste(pdf_path):
    """Prüft ob die PDF eine gültige Abmeldeliste ist. Gibt (ok, fehler) zurück."""
    try:
        reader = PdfReader(pdf_path)
        text = '\n'.join(page.extract_text() or '' for page in reader.pages)
    except Exception:
        return False, 'Die Abmeldeliste konnte nicht gelesen werden.'
    if not re.search(r'^0\d{2}', text, re.MULTILINE):
        return False, 'Die hochgeladene Datei ist keine gültige Abmeldeliste (keine Positionszeilen gefunden).'
    if not re.search(r'\d{11}', text):
        return False, 'Die hochgeladene Datei ist keine gültige Abmeldeliste (keine Sendungsnummern gefunden).'
    return True, None


def _validate_t1(pdf_path, filename=''):
    """Prüft ob die PDF ein gültiges T1-Transitdokument ist. Gibt (ok, fehler) zurück."""
    try:
        reader = PdfReader(pdf_path)
        text = '\n'.join(page.extract_text() or '' for page in reader.pages)
    except Exception:
        return False, f'"{filename}" konnte nicht gelesen werden.'
    has_mrn = bool(re.search(r'\d{2}[A-Z]{2}[A-Z0-9]{14,}', text))
    has_keywords = any(kw in text for kw in ['Packst. insgesamt', 'Gesamte Rohmasse', 'BESTIMMUNGSSTELLE'])
    if not (has_mrn and has_keywords):
        return False, f'"{filename}" ist kein gültiges T1-Transitdokument.'
    return True, None



@login_required(login_url='login')
def main(request):
    data = None
    summary = None
    excel_path = None
    error_message = None
    report = None
    
    # Nur benutzerspezifische Daten anzeigen (oder alle für Superuser)
    if request.user.is_superuser:
        abfahrten = Abfahrt.objects.all().order_by('name')
        zollamt_abgang_qs = Zollamt.objects.filter(typ='abgang').order_by('name')
        zollamt_grenz_qs = Zollamt.objects.filter(typ='grenz').order_by('name')
    else:
        abfahrten = Abfahrt.objects.filter(created_by=request.user).order_by('name')
        zollamt_abgang_qs = Zollamt.objects.filter(typ='abgang', created_by=request.user).order_by('name')
        zollamt_grenz_qs = Zollamt.objects.filter(typ='grenz', created_by=request.user).order_by('name')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'generate_wa':
            abfahrt_id = request.POST.get('abfahrt_id')
            datum = request.POST.get('datum')
            zollamt_abgang_id = request.POST.get('zollamt_abgang')
            zollamt_grenz_id = request.POST.get('zollamt_grenz')
            zollamt_abgang = Zollamt.objects.filter(id=zollamt_abgang_id).first() if zollamt_abgang_id else None
            zollamt_grenz = Zollamt.objects.filter(id=zollamt_grenz_id).first() if zollamt_grenz_id else None
            abfahrt = Abfahrt.objects.filter(id=abfahrt_id).first()
            abmeldeliste_file = request.FILES.get('abmeldeliste_pdf')
            target_dir = os.path.join(settings.BASE_DIR, 'Python_Back_End', 'loading_list_check')
            temp_path = os.path.join(target_dir, 'abmeldeliste.pdf')
            if abmeldeliste_file:
                try:
                    if not _is_pdf(abmeldeliste_file):
                        error_message = 'Nur PDF-Dateien sind erlaubt (Abmeldeliste).'
                        return render(request, 'main/main.html', {
                            'data': data, 'summary': summary, 'report': report,
                            'error_message': error_message, 'abfahrten': abfahrten,
                        })
                    os.makedirs(target_dir, exist_ok=True)
                    with open(temp_path, 'wb+') as destination:
                        for chunk in abmeldeliste_file.chunks():
                            destination.write(chunk)
                except Exception as e:
                    error_message = f'Fehler beim Speichern der PDF: {e}'
                    return render(request, 'main/main.html', {
                        'data': data,
                        'summary': summary,
                        'report': report,
                        'error_message': error_message,
                        'abfahrten': abfahrten,
                    })
            if abfahrt:
                if os.path.exists(temp_path):
                    ok, err = _validate_abmeldeliste(temp_path)
                    if not ok:
                        error_message = err
                    else:
                        shipment_list = Shipment.create_shipment(temp_path)
                    if not error_message and shipment_list:
                        # Alte Sendungen dieses Users löschen (temporäre Daten pro WA-Erstellung)
                        ShipmentModel.objects.filter(user=request.user).delete()

                        # Sendungen aus PDF in DB speichern
                        for s in shipment_list:
                            s_no = str(s.shipment_no).strip() if s.shipment_no else None
                            if not s_no or len(s_no) != 11:
                                continue
                            db_shipment = ShipmentModel.objects.create(
                                shipment_number=s_no,
                                sender=str(s.exporter).strip() if s.exporter else None,
                                user=request.user,
                            )
                            if s.colli_no or s.colli_type:
                                Colli.objects.create(
                                    quantity=s.colli_no or 0,
                                    type=str(s.colli_type).strip() if s.colli_type else None,
                                    weight=float(s.weight) if s.weight else None,
                                    shipment=db_shipment,
                                )

                        # --- T1-Dokumente verarbeiten und mit Sendungen verknüpfen ---
                        TransitDocument.objects.filter(user=request.user).delete()
                        t1_files = request.FILES.getlist('files[]')
                        for t1_file in t1_files:
                            t1_temp_dir = os.path.join(settings.BASE_DIR, 'Python_Back_End', 't1_reader')
                            os.makedirs(t1_temp_dir, exist_ok=True)
                            t1_temp_path = os.path.join(t1_temp_dir, f'temp_{t1_file.name}')
                            try:
                                if not _is_pdf(t1_file):
                                    error_message = f'"{t1_file.name}": Nur PDF-Dateien sind erlaubt.'
                                    break
                                with open(t1_temp_path, 'wb+') as f:
                                    for chunk in t1_file.chunks():
                                        f.write(chunk)
                                ok, err = _validate_t1(t1_temp_path, t1_file.name)
                                if not ok:
                                    error_message = err
                                    break
                                t1_result, t1_err = t1_data_filter(t1_temp_path)
                                if t1_err or not t1_result:
                                    continue
                                mrn = t1_result.get('MRN-Nummer')
                                if not mrn:
                                    continue
                                t1_colli_str = t1_result.get('Anzahl Packstücke')
                                t1_colli_qty = int(t1_colli_str) if t1_colli_str else 0
                                t1_weight_raw = str(t1_result.get('Gewicht') or '0')
                                t1_weight_str = t1_weight_raw.replace('’', '').replace("'", '')
                                try:
                                    t1_weight = float(t1_weight_str)
                                except ValueError:
                                    t1_weight = None
                                transit_doc, _ = TransitDocument.objects.update_or_create(
                                    t_number=mrn,
                                    defaults={
                                        't_colli_quantity': t1_colli_qty,
                                        't_weight': t1_weight,
                                        't_customs_office': t1_result.get('Zollstelle'),
                                        'user': request.user,
                                    }
                                )
                                t1_sendung_no = t1_result.get('Sendungsnummer')
                                if t1_sendung_no:
                                    ShipmentModel.objects.filter(
                                        shipment_number=t1_sendung_no,
                                        user=request.user
                                    ).update(transit=transit_doc)
                            except Exception:
                                continue

                        # --- Report ---
                        report_lines = []

                        # 1. Zollabfertigung
                        for shipment in shipment_list:
                            customs_text = ' '.join(str(x) for x in shipment.customs_handling)
                            if 'Missing customs handling' in customs_text:
                                line_no = str(shipment.position).strip() or '-'
                                s_no = str(shipment.shipment_no).strip() or '-'
                                report_lines.append(f'[Customs Handling fehlt]    Pos. {line_no} / Sendung {s_no}')

                        # 2. T1-Status pro Sendung
                        for s in shipment_list:
                            s_no = str(s.shipment_no).strip() if s.shipment_no else None
                            if not s_no:
                                continue
                            try:
                                db_s = ShipmentModel.objects.get(shipment_number=s_no, user=request.user)
                                transit = db_s.transit
                                if transit is None:
                                    report_lines.append(f'[T1 fehlt]      Sendung {s_no}')
                                else:
                                    colli_sum = db_s.collis.aggregate(total=Sum('quantity'))['total'] or 0
                                    if colli_sum != transit.t_colli_quantity:
                                        report_lines.append(
                                            f'[T1 Differenz] Sendung {s_no}: Packstücke — Liste: {colli_sum}, T1: {transit.t_colli_quantity}'
                                        )
                                    weight_sum = db_s.collis.aggregate(total=Sum('weight'))['total'] or 0
                                    if round(weight_sum, 3) != round(transit.t_weight or 0, 3):
                                        report_lines.append(
                                            f'[T1 Differenz] Sendung {s_no}: Gewicht — Liste: {weight_sum:.3f} kg, T1: {transit.t_weight} kg'
                                        )
                            except ShipmentModel.DoesNotExist:
                                pass

                        # 3. Überschüssige T1s (hochgeladen aber keine Sendung auf der Liste)
                        for td in TransitDocument.objects.filter(user=request.user):
                            if not ShipmentModel.objects.filter(transit=td, user=request.user).exists():
                                report_lines.append(f'[T1 Überzählig]  MRN {td.t_number} — keine Sendung auf der Liste')

                        # 4. Gesamtdifferenz Liste vs. alle T1-Dokumente
                        liste_collis  = sum(s.colli_no for s in shipment_list if s.colli_no)
                        liste_gewicht = sum(s.weight   for s in shipment_list if s.weight)
                        t1_collis  = TransitDocument.objects.filter(user=request.user).aggregate(total=Sum('t_colli_quantity'))['total'] or 0
                        t1_gewicht = TransitDocument.objects.filter(user=request.user).aggregate(total=Sum('t_weight'))['total'] or 0
                        diff_collis  = liste_collis - t1_collis
                        diff_gewicht = round(liste_gewicht - t1_gewicht, 3)
                        report_lines.append('─' * 50)
                        report_lines.append(f'[Summe Abmeldeliste]   Packstücke: {liste_collis}  |  Gewicht: {liste_gewicht:.3f} kg')
                        report_lines.append(f'[Summe aller T1]      Packstücke: {t1_collis}  |  Gewicht: {t1_gewicht:.3f} kg')
                        if diff_collis != 0 or diff_gewicht != 0:
                            report_lines.append(f'[DIFFERENZ]     Packstücke: {diff_collis:+d}  |  Gewicht: {diff_gewicht:+.3f} kg')
                        else:
                            report_lines.append('[DIFFERENZ]     ✓ Packstücke und Gewicht stimmen überein')

                        if report_lines:
                            report = '\n'.join(report_lines)
                        else:
                            report = '✓ Alles in Ordnung – keine Abweichungen gefunden.'

                        shipment_list[0].shipment_list = shipment_list
                        # Excel schreiben
                        buffer, filename = shipment_list[0].create_excel(
                            abfahrt_name=abfahrt.name,
                            datum=datum,
                            kennzeichen=abfahrt.kennzeichen,
                            anhaenger=abfahrt.anhaenger,
                            zollamt_abgang=str(zollamt_abgang.name) if zollamt_abgang else '',
                            zollamt_grenz=str(zollamt_grenz.name) if zollamt_grenz else ''
                        )
                        excel_bytes = base64.b64encode(buffer.getvalue()).decode()
                        request.session['excel_data'] = excel_bytes
                        request.session['excel_filename'] = filename
                        # Vorschau generieren (gleiche Sortierung wie Excel)
                        def is_et1_durchgehend(s):
                            tokens = s.customs_handling
                            return ('E-T1' in tokens
                                    and 'GVZ' not in tokens
                                    and 'EU-VZ' not in tokens
                                    and 'EUVZ' not in tokens
                                    and 'S-T1' not in tokens)

                        top_group    = [s for s in shipment_list if is_et1_durchgehend(s)]
                        bottom_group = [s for s in shipment_list if not is_et1_durchgehend(s)]

                        def shipment_to_row(s, gruppe=''):
                            return {
                                'Gruppe': gruppe,
                                'Sendungsnummer': s.shipment_no,
                                'Exporteur': s.exporter,
                                'Colli': s.colli_no,
                                'Typ': s.colli_type,
                                'Inhalt': s.content,
                                'Gewicht': s.weight,
                                'Zollabfertigung': ' '.join(s.customs_handling),
                            }

                        rows = [shipment_to_row(s, 'E-T1 durchgehend') for s in top_group]
                        if top_group and bottom_group:
                            zollamt_abgang_name = str(zollamt_abgang.name) if zollamt_abgang else ''
                            rows.append({'Gruppe': '---', 'Sendungsnummer': zollamt_abgang_name,
                                         'Exporteur': '', 'Colli': '', 'Typ': '', 'Inhalt': '', 'Gewicht': '', 'Zollabfertigung': ''})
                            rows.append({'Gruppe': '---', 'Sendungsnummer': 'A-Nummer (Grenzverzollung)',
                                         'Exporteur': '', 'Colli': '', 'Typ': '', 'Inhalt': '', 'Gewicht': '', 'Zollabfertigung': ''})
                        rows += [shipment_to_row(s, 'S-T1 / Grenze') for s in bottom_group]

                        df = pd.DataFrame(rows)
                        data = df.to_html(classes='table table-striped a4-size', index=False)
                        sum_collies = Shipment.calculate_total_collies(shipment_list)
                        sum_weight = Shipment.calculate_total_weight(shipment_list)
                        summary = f'Summe der Collies: {sum_collies} und Gewicht: {sum_weight}'
                    else:
                        error_message = 'Keine Daten aus der PDF extrahiert. Bitte prüfe die Datei.'
                else:
                    error_message = 'Keine Abmeldeliste gefunden. Bitte zuerst PDF hochladen.'
            else:
                error_message = 'Abfahrt nicht gefunden.'

    return render(request, 'main/main.html', {
        'data': data,
        'summary': summary,
        'report': report,
        'error_message': error_message,
        'abfahrten': abfahrten,
        'zollamt_abgang': zollamt_abgang_qs,
        'zollamt_grenz': zollamt_grenz_qs,
        'user': request.user,
        'excel_filename': request.session.get('excel_filename', ''),
    })




@login_required(login_url='login')
def download_excel(request):
    excel_data = request.session.get('excel_data')
    filename = request.session.get('excel_filename', 'Warenausweis.xlsx')
    if not excel_data:
        raise Http404
    buffer = BytesIO(base64.b64decode(excel_data))
    return FileResponse(buffer, as_attachment=True, filename=filename)




