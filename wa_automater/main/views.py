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

from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required


@csrf_exempt
@login_required(login_url='login')
def settings_view(request):
    abfahrten = Abfahrt.objects.all().order_by('name')
    zollämter = Zollamt.objects.all().order_by('typ', 'name')
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        if form_type == 'add_abfahrt':
            name = request.POST.get('abfahrt_name')
            kennzeichen = request.POST.get('abfahrt_kennzeichen')
            anhaenger = request.POST.get('abfahrt_anhaenger')
            if name and kennzeichen:
                Abfahrt.objects.create(name=name, kennzeichen=kennzeichen, anhaenger=anhaenger)
            return redirect('settings')
        elif form_type == 'delete_abfahrt':
            abfahrt_id = request.POST.get('delete_abfahrt_id')
            if abfahrt_id:
                Abfahrt.objects.filter(id=abfahrt_id).delete()
            return redirect('settings')
        elif form_type == 'add_zollamt':
            name = request.POST.get('zollamt_name')
            typ = request.POST.get('zollamt_typ')
            if name and typ:
                Zollamt.objects.create(name=name, typ=typ)
            return redirect('settings')
        elif form_type == 'delete_zollamt':
            zollamt_id = request.POST.get('delete_zollamt_id')
            if zollamt_id:
                Zollamt.objects.filter(id=zollamt_id).delete()
            return redirect('settings')
    return render(request, 'main/settings.html', {
        'abfahrten': abfahrten,
        'zollämter': zollämter,
        'user': request.user,
    })

@login_required(login_url='login')
def main(request):
    data = None
    summary = None
    error_message = None
    abfahrten = Abfahrt.objects.all().order_by('name')
    zollamt_abgang_qs = Zollamt.objects.filter(typ='abgang').order_by('name')
    zollamt_grenz_qs = Zollamt.objects.filter(typ='grenz').order_by('name')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_abfahrt':
            name = request.POST.get('abfahrt_name')
            kennzeichen = request.POST.get('abfahrt_kennzeichen')
            anhaenger = request.POST.get('abfahrt_anhaenger')
            if name and kennzeichen:
                Abfahrt.objects.create(name=name, kennzeichen=kennzeichen, anhaenger=anhaenger)
            return redirect('main')
        elif action == 'delete_abfahrt':
            abfahrt_id = request.POST.get('delete_abfahrt_id')
            if abfahrt_id:
                Abfahrt.objects.filter(id=abfahrt_id).delete()
            return redirect('main')
        elif action == 'upload_abmeldeliste':
            abmeldeliste_file = request.FILES.get('abmeldeliste_pdf')
            if abmeldeliste_file:
                try:
                    target_dir = os.path.join(settings.BASE_DIR, 'Python_Back_End', 'loading_list_check')
                    target_dir = os.path.abspath(target_dir)
                    os.makedirs(target_dir, exist_ok=True)
                    temp_path = os.path.join(target_dir, 'abmeldeliste.pdf')
                    with open(temp_path, 'wb+') as destination:
                        for chunk in abmeldeliste_file.chunks():
                            destination.write(chunk)
                    shipment_list = Shipment.create_shipment(temp_path)
                    if shipment_list:
                        shipment_list[0].shipment_list = shipment_list
                        shipment_list[0].create_excel()
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
                except Exception as e:
                    error_message = f'Fehler beim Verarbeiten der PDF: {e}'
            else:
                error_message = 'Keine Datei empfangen. Bitte wähle eine PDF aus.'
        elif action == 'generate_wa':
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
                        'error_message': error_message,
                        'abfahrten': abfahrten,
                    })
            if abfahrt:
                if os.path.exists(temp_path):
                    shipment_list = Shipment.create_shipment(temp_path)
                    if shipment_list:
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