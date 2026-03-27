from django.shortcuts import render, redirect
import pandas as pd
import os
from django.conf import settings
import sys
import pathlib
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR / 'Python_Back_End' / 'loading_list_check'))
from CustomsList import Shipment
from .models import Abfahrt, Zollamt

from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required


@login_required(login_url='login')
def main(request):
    data = None
    summary = None
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
                    shipment_list = Shipment.create_shipment(temp_path)
                    if shipment_list:
                        report_lines = []
                        for shipment in shipment_list:
                            customs_text = ' '.join(str(x) for x in shipment.customs_handling)
                            if 'No customs handling' in customs_text:
                                line_no = str(shipment.position).strip() or '-'
                                shipment_no = str(shipment.shipment_no).strip() or '-'
                                report_lines.append(
                                    f'Missing customs handling in Line No. {line_no} shipment no. {shipment_no}'
                                )

                        if report_lines:
                            report = '\n'.join(report_lines)
                        else:
                            report = 'No customs handling issues found.'

                        shipment_list[0].shipment_list = shipment_list
                        # Excel schreiben
                        shipment_list[0].create_excel(
                            abfahrt_name=abfahrt.name,
                            datum=datum,
                            kennzeichen=abfahrt.kennzeichen,
                            anhaenger=abfahrt.anhaenger,
                            zollamt_abgang=str(zollamt_abgang.name) if zollamt_abgang else '',
                            zollamt_grenz=str(zollamt_grenz.name) if zollamt_grenz else ''
                        )
                        # Vorschau generieren
                        df = pd.DataFrame([
                            {
                                'Position': s.position,
                                'Sendungsnummer': s.shipment_no,
                                'Exporteur': s.exporter,
                                'Colli': s.colli_no,
                                'Typ': s.colli_type,
                                'Inhalt': s.content,
                                'Gewicht': s.weight,
                                'Zollabfertigung': s.customs_handling
                            } for s in shipment_list
                        ])
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
    })


def user_login(request):
    user = User.objects.create_user("john", "lennon@thebeatles.com", "johnpassword")

    user.last_name = "Lennon"
    user.save()