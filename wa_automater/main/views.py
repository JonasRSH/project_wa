from django.shortcuts import render, redirect
import pandas as pd
import os
import re
from django.conf import settings
import sys
import pathlib
from pypdf import PdfReader
from django.contrib import messages
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


def _cleanup_uploaded_files():
    """Entfernt temporäre Upload-Dateien aus den Parser-Arbeitsordnern."""
    cleanup_specs = [
        (os.path.join(settings.BASE_DIR, 'Python_Back_End', 'loading_list_check'), ('abmeldeliste.pdf',)),
        (os.path.join(settings.BASE_DIR, 'Python_Back_End', 't1_reader'), ('temp_*.pdf',)),
    ]

    for folder, patterns in cleanup_specs:
        if not os.path.isdir(folder):
            continue
        for pattern in patterns:
            for file_path in pathlib.Path(folder).glob(pattern):
                try:
                    file_path.unlink(missing_ok=True)
                except OSError:
                    continue


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
                                t1_colli_type = t1_result.get('Colli-Typ')
                                t1_goods_description = t1_result.get('Warenbeschreibung')
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
                                        't_colli_type': t1_colli_type,
                                        't_goods_description': t1_goods_description,
                                        't_weight': t1_weight,
                                        't_customs_office': t1_result.get('Zollstelle'),
                                        'user': request.user,
                                    }
                                )
                                # Sendungen via EXPO-Referenzen verknüpfen (E-T1 und S-T1)
                                expo_nos = t1_result.get('Sendungsnummern', [])
                                if expo_nos:
                                    for expo_no in expo_nos:
                                        ShipmentModel.objects.filter(
                                            shipment_number=expo_no,
                                            user=request.user
                                        ).update(transit=transit_doc)
                                else:
                                    t1_sendung_no = t1_result.get('Sendungsnummer')
                                    if t1_sendung_no:
                                        ShipmentModel.objects.filter(
                                            shipment_number=t1_sendung_no,
                                            user=request.user
                                        ).update(transit=transit_doc)
                            except Exception:
                                continue

                        # --- Report (HTML) ---
                        # Hilfsfunktionen für farbige Report-Zeilen
                        def _rh(title):
                            return (f'<div style="font-weight:bold;color:#fff;background:#0070c0;'
                                    f'padding:4px 10px;border-radius:3px;margin:10px 0 3px;">'
                                    f'{title}</div>')
                        def _rok(msg):
                            return f'<div style="padding:2px 10px;color:#198754;">&#10003;&nbsp;{msg}</div>'
                        def _rerr(msg):
                            return (f'<div style="padding:2px 10px;color:#dc3545;'
                                    f'font-weight:bold;">&#10007;&nbsp;{msg}</div>')
                        def _rwarn(msg):
                            return (f'<div style="padding:2px 10px;color:#e07b00;'
                                    f'font-weight:bold;">&#9888;&nbsp;{msg}</div>')
                        def _rdet(label, val):
                            return (f'<div style="padding:1px 10px 1px 28px;color:#6c757d;">'
                                    f'<span style="display:inline-block;min-width:80px;">{label}</span>'
                                    f'{val}</div>')

                        report_parts = []

                        def is_et1_durchgehend(s):
                            tokens = s.customs_handling
                            return ('E-T1' in tokens
                                    and 'GVZ' not in tokens
                                    and 'EU-VZ' not in tokens
                                    and 'EUVZ' not in tokens
                                    and 'ATA' not in tokens
                                    and 'S-T1' not in tokens)

                        # 1. Zollabfertigung
                        customs_parts = []
                        for shipment in shipment_list:
                            customs_text = ' '.join(str(x) for x in shipment.customs_handling)
                            if 'Missing customs handling' in customs_text:
                                line_no = str(shipment.position).strip() or '-'
                                s_no = str(shipment.shipment_no).strip() or '-'
                                customs_parts.append(_rwarn(f'Pos.&nbsp;{line_no}&nbsp;&nbsp;|&nbsp;&nbsp;Sendung&nbsp;{s_no}'))
                        if customs_parts:
                            report_parts.append(_rh('&#9888; ZOLLABFERTIGUNG PRÜFEN'))
                            report_parts.extend(customs_parts)

                        # 2. E-T1 Sendungen
                        et1_durchgehend_list = [s for s in shipment_list if is_et1_durchgehend(s)]
                        et1_grenze_list      = [s for s in shipment_list
                                                if 'E-T1' in s.customs_handling
                                                and not is_et1_durchgehend(s)]
                        et1_shipments = et1_durchgehend_list + et1_grenze_list
                        et1_parts = []
                        for s in et1_shipments:
                            s_no = str(s.shipment_no).strip() if s.shipment_no else None
                            if not s_no:
                                continue
                            absender = s.exporter or ''
                            try:
                                db_s = ShipmentModel.objects.get(shipment_number=s_no, user=request.user)
                                if db_s.transit is None:
                                    et1_parts.append(_rerr(f'T1 fehlt&nbsp;&nbsp;{s_no}&nbsp;&nbsp;|&nbsp;&nbsp;{absender}'))
                                else:
                                    t1_colli = db_s.transit.t_colli_quantity
                                    t1_w = db_s.transit.t_weight
                                    diffs = []
                                    if t1_colli is not None and t1_colli != (s.colli_no or 0):
                                        delta = t1_colli - (s.colli_no or 0)
                                        diffs.append(_rdet('Colli:',
                                            f'<span style="color:#dc3545;">T1={t1_colli}&nbsp;/&nbsp;'
                                            f'Liste={s.colli_no}&nbsp;&nbsp;'
                                            f'<b>(&Delta;&nbsp;{delta:+d})</b></span>'))
                                    if t1_w is not None and s.weight:
                                        delta_w = round(t1_w - s.weight, 3)
                                        if abs(delta_w) > 0.01:
                                            diffs.append(_rdet('Gewicht:',
                                                f'<span style="color:#dc3545;">T1={t1_w:.3f}&nbsp;kg&nbsp;/&nbsp;'
                                                f'Liste={s.weight}&nbsp;kg&nbsp;&nbsp;'
                                                f'<b>(&Delta;&nbsp;{delta_w:+.3f}&nbsp;kg)</b></span>'))
                                    if diffs:
                                        et1_parts.append(_rwarn(f'Differenz&nbsp;&nbsp;{s_no}&nbsp;&nbsp;|&nbsp;&nbsp;{absender}'))
                                        et1_parts.extend(diffs)
                            except ShipmentModel.DoesNotExist:
                                pass
                        if et1_shipments:
                            n_total = len(et1_shipments)
                            n_durch = len(et1_durchgehend_list)
                            n_grenz = len(et1_grenze_list)
                            sub = ''
                            if n_durch and n_grenz:
                                sub = f'&nbsp;&nbsp;&mdash;&nbsp;&nbsp;{n_durch} Durchgehend&nbsp;&nbsp;|&nbsp;&nbsp;{n_grenz} Grenzverzollung'
                            elif n_durch:
                                sub = f'&nbsp;&nbsp;&mdash;&nbsp;&nbsp;{n_durch} Durchgehend'
                            elif n_grenz:
                                sub = f'&nbsp;&nbsp;&mdash;&nbsp;&nbsp;{n_grenz} Grenzverzollung'
                            report_parts.append(_rh(f'E-T1 SENDUNGEN ({n_total}){sub}'))
                            if et1_parts:
                                report_parts.extend(et1_parts)
                            else:
                                report_parts.append(_rok('Alle E-T1 Dokumente vollständig und korrekt'))

                        # 2b. S-T1 Gruppenprüfung
                        _ST1_TOKENS = frozenset({'GVZ', 'EU-VZ', 'EUVZ'})
                        s_t1_all = [s for s in shipment_list
                                    if 'E-T1' not in s.customs_handling
                                    and _ST1_TOKENS.intersection(s.customs_handling)]
                        if s_t1_all:
                            s_t1_total  = len(s_t1_all)
                            s_t1_linked = sum(
                                1 for s in s_t1_all
                                if (sno := str(s.shipment_no).strip() if s.shipment_no else None)
                                and ShipmentModel.objects.filter(
                                    shipment_number=sno, user=request.user, transit__isnull=False
                                ).exists()
                            )
                            report_parts.append(_rh(f'S-T1 GRUPPE ({s_t1_total} Sendungen)'))
                            if s_t1_linked == s_t1_total:
                                report_parts.append(_rok(f'{s_t1_total}/{s_t1_total} Sendungen auf S-T1 verknüpft'))
                            else:
                                missing = s_t1_total - s_t1_linked
                                report_parts.append(_rerr(f'{s_t1_linked}/{s_t1_total} Sendungen auf S-T1 &mdash; {missing} fehlen'))
                            st1_transit = next(
                                (ShipmentModel.objects.filter(
                                    shipment_number=str(s.shipment_no).strip(), user=request.user
                                ).select_related('transit').first().transit
                                 for s in s_t1_all
                                 if s.shipment_no
                                 and ShipmentModel.objects.filter(
                                     shipment_number=str(s.shipment_no).strip(),
                                     user=request.user, transit__isnull=False
                                 ).exists()),
                                None
                            )
                            if st1_transit:
                                abm_colli  = sum(s.colli_no or 0 for s in s_t1_all)
                                abm_weight = sum(s.weight   or 0 for s in s_t1_all)
                                tc, tw = st1_transit.t_colli_quantity, st1_transit.t_weight
                                if tc is not None:
                                    if tc != abm_colli:
                                        delta = tc - abm_colli
                                        report_parts.append(_rdet('Colli:',
                                            f'<span style="color:#dc3545;">T1={tc}&nbsp;/&nbsp;'
                                            f'Liste={abm_colli}&nbsp;&nbsp;<b>(&Delta;&nbsp;{delta:+d})</b></span>'))
                                    else:
                                        report_parts.append(_rdet('Colli:', f'{tc} &#10003;'))
                                if tw is not None and abm_weight:
                                    delta_w = round(tw - abm_weight, 3)
                                    if abs(delta_w) > 0.01:
                                        report_parts.append(_rdet('Gewicht:',
                                            f'<span style="color:#dc3545;">T1={tw:.3f}&nbsp;kg&nbsp;/&nbsp;'
                                            f'Liste={abm_weight}&nbsp;kg&nbsp;&nbsp;<b>(&Delta;&nbsp;{delta_w:+.3f}&nbsp;kg)</b></span>'))
                                    else:
                                        report_parts.append(_rdet('Gewicht:', f'{tw:.3f}&nbsp;kg &#10003;'))

                        # 3. Gesamtsumme
                        liste_collis  = sum(s.colli_no for s in shipment_list if s.colli_no)
                        liste_gewicht = sum(s.weight   for s in shipment_list if s.weight)
                        t1_collis  = TransitDocument.objects.filter(user=request.user).aggregate(total=Sum('t_colli_quantity'))['total'] or 0
                        t1_gewicht = TransitDocument.objects.filter(user=request.user).aggregate(total=Sum('t_weight'))['total'] or 0
                        diff_collis  = liste_collis  - t1_collis
                        diff_gewicht = round(liste_gewicht - t1_gewicht, 3)
                        report_parts.append(_rh('GESAMTSUMME'))
                        report_parts.append(
                            f'<table style="width:100%;font-size:0.83rem;border-collapse:collapse;margin:2px 0;">'
                            f'<tr style="border-bottom:1px solid #dee2e6;">'
                            f'<td style="padding:3px 10px;color:#6c757d;">Abmeldeliste</td>'
                            f'<td style="padding:3px 10px;text-align:right;">{liste_collis}&nbsp;Packstücke</td>'
                            f'<td style="padding:3px 10px;text-align:right;">{liste_gewicht:.3f}&nbsp;kg</td></tr>'
                            f'<tr style="border-bottom:1px solid #dee2e6;">'
                            f'<td style="padding:3px 10px;color:#6c757d;">T1&nbsp;Dokumente</td>'
                            f'<td style="padding:3px 10px;text-align:right;">{t1_collis}&nbsp;Packstücke</td>'
                            f'<td style="padding:3px 10px;text-align:right;">{t1_gewicht:.3f}&nbsp;kg</td></tr>'
                        )
                        if diff_collis != 0 or diff_gewicht != 0:
                            colli_cell = (f'<span style="color:#dc3545;font-weight:bold;">&Delta;&nbsp;{diff_collis:+d}&nbsp;Packstücke</span>')
                            weight_cell = (f'<span style="color:#dc3545;font-weight:bold;">&Delta;&nbsp;{diff_gewicht:+.3f}&nbsp;kg</span>')
                            report_parts.append(
                                f'<tr><td style="padding:3px 10px;color:#6c757d;">Differenz</td>'
                                f'<td style="padding:3px 10px;text-align:right;">{colli_cell}</td>'
                                f'<td style="padding:3px 10px;text-align:right;">{weight_cell}</td></tr>'
                                f'</table>'
                            )
                        else:
                            report_parts.append(
                                f'<tr><td colspan="3" style="padding:3px 10px;color:#198754;">'
                                f'&#10003;&nbsp;Packstücke und Gewicht stimmen überein</td></tr></table>'
                            )

                        report = ''.join(report_parts) if report_parts else _rok('Alles in Ordnung &ndash; keine Abweichungen gefunden.')

                        shipment_list[0].shipment_list = shipment_list

                        # MRN aus verknüpften T1-Dokumenten an jedes Shipment-Objekt hängen
                        # (wird in create_excel statt der Sendungsnummer eingetragen)
                        for s in shipment_list:
                            s_no = str(s.shipment_no).strip() if s.shipment_no else None
                            s.mrn = None
                            s.t1_colli_no = None
                            s.t1_colli_type = None
                            s.t1_goods_description = None
                            s.t1_weight = None
                            s.t1_customs_office = None
                            if s_no:
                                db_s = ShipmentModel.objects.filter(
                                    shipment_number=s_no, user=request.user
                                ).select_related('transit').first()
                                if db_s and db_s.transit:
                                    s.mrn = db_s.transit.t_number
                                    s.t1_colli_no = db_s.transit.t_colli_quantity
                                    s.t1_colli_type = db_s.transit.t_colli_type
                                    s.t1_goods_description = db_s.transit.t_goods_description
                                    s.t1_weight = db_s.transit.t_weight
                                    s.t1_customs_office = db_s.transit.t_customs_office

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
                        top_group    = [s for s in shipment_list if is_et1_durchgehend(s)]
                        bottom_group = [s for s in shipment_list if not is_et1_durchgehend(s)]

                        def shipment_to_row(s, gruppe=''):
                            mrn = getattr(s, 'mrn', None)
                            t1_colli = getattr(s, 't1_colli_no', None)
                            t1_colli_type = getattr(s, 't1_colli_type', None)
                            t1_goods_description = getattr(s, 't1_goods_description', None)
                            t1_weight = getattr(s, 't1_weight', None)
                            # Sendungsnummer: MRN anzeigen falls vorhanden,
                            # sonst Sendungsnummer in fett rot (kein T1 verknüpft)
                            if mrn:
                                sno_display = mrn
                            else:
                                sno_display = (
                                    f'<span class="wa-preview-warning">'
                                    f'{s.shipment_no}</span>'
                                )
                            # Zollabfertigung: fehlende Customs-Handling-Warnung fett rot hervorheben
                            customs_str = ' '.join(s.customs_handling)
                            if 'No customs handling' in customs_str:
                                customs_display = (
                                    f'<span class="wa-preview-warning">{customs_str}</span>'
                                )
                            else:
                                customs_display = customs_str
                            return {
                                'Gruppe': gruppe,
                                'Sendungsnummer': sno_display,
                                'Exporteur': s.exporter if s.exporter else '',
                                'Colli': t1_colli if t1_colli is not None else '',
                                'Typ': t1_colli_type or (s.colli_type if s.colli_type else 'PK'),
                                'Inhalt': t1_goods_description if t1_goods_description else (s.content or ''),
                                'Gewicht': t1_weight if t1_weight is not None else '',
                                'Zollabfertigung': customs_display,
                            }

                        rows = [shipment_to_row(s, 'E-T1 durchgehend') for s in top_group]
                        if top_group and bottom_group:
                            zollamt_abgang_name = str(zollamt_abgang.name) if zollamt_abgang else ''
                            rows.append({'Gruppe': '---', 'Sendungsnummer': zollamt_abgang_name,
                                         'Exporteur': '', 'Colli': '', 'Typ': '', 'Inhalt': '', 'Gewicht': '', 'Zollabfertigung': ''})
                            rows.append({'Gruppe': '---', 'Sendungsnummer': 'A-Nummer (Grenzverzollung)',
                                         'Exporteur': '', 'Colli': '', 'Typ': '', 'Inhalt': '', 'Gewicht': '', 'Zollabfertigung': ''})
                        # S-T1-Gruppe = bottom_group ohne E-T1 (GVZ, EU-VZ, VZ AUF …) → eine Zeile
                        # E-T1 Grenze = bottom_group mit E-T1 (eigenes Transitdokument) → einzeln
                        s_t1_group = [s for s in bottom_group if 'E-T1' not in s.customs_handling]
                        other_bottom = [s for s in bottom_group if 'E-T1' in s.customs_handling]
                        st1_rep = next((s for s in s_t1_group if getattr(s, 'mrn', None)), None)
                        if st1_rep:
                            rows.append({
                                'Gruppe': 'S-T1 / Grenze',
                                'Sendungsnummer': st1_rep.mrn,
                                'Exporteur': 'Diverse',
                                'Colli': getattr(st1_rep, 't1_colli_no', '') or '',
                                'Typ': st1_rep.colli_type if st1_rep.colli_type else 'PK',
                                'Inhalt': 'Stückgut',
                                'Gewicht': getattr(st1_rep, 't1_weight', '') or '',
                                'Zollabfertigung': 'S-T1',
                            })
                        elif s_t1_group:
                            rows.append({
                                'Gruppe': 'S-T1 / Grenze',
                                'Sendungsnummer': '<span class="wa-preview-warning">S-T1 fehlt</span>',
                                'Exporteur': '', 'Colli': '', 'Typ': '', 'Inhalt': '', 'Gewicht': '',
                                'Zollabfertigung': '<span class="wa-preview-warning">S-T1 nicht hochgeladen</span>',
                            })
                        seen_mrns = set()
                        for s in other_bottom:
                            mrn = getattr(s, 'mrn', None)
                            if mrn and mrn in seen_mrns:
                                continue
                            if mrn:
                                seen_mrns.add(mrn)
                            rows.append(shipment_to_row(s, 'E-T1 Grenze'))

                        df = pd.DataFrame(rows).drop(columns=['Gruppe'])
                        # escape=False damit die HTML-Spans gerendert werden
                        data = df.to_html(classes='table table-striped a4-size', index=False, escape=False)
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


@login_required(login_url='login')
def clear_uploaded_data(request):
    if request.method != 'POST':
        return redirect('main')

    try:
        # Alle benutzerspezifischen WA-/T1-Daten entfernen.
        ShipmentModel.objects.filter(user=request.user).delete()
        TransitDocument.objects.filter(user=request.user).delete()
        _cleanup_uploaded_files()

        request.session.pop('excel_data', None)
        request.session.pop('excel_filename', None)
        messages.success(request, 'Alle Upload- und Transitdaten wurden gelöscht.')
    except Exception:
        # Kein 500 für Anwender, stattdessen sauber zurück auf die Hauptseite.
        messages.error(request, 'Die Daten konnten nicht vollständig gelöscht werden. Bitte erneut versuchen.')

    return redirect('main')




