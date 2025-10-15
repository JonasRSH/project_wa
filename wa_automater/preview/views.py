from django.shortcuts import render
import pandas as pd
import os
from django.conf import settings

import sys
import pathlib
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR / 'Python_Back_End/loading_list_check'))
from CustomsList import Shipment


def preview_excel(request):
    # Path to your Excel file
    excel_file_path = os.path.join(settings.BASE_DIR, 'templates/preview/Warenausweis_HUB-Lyss.xls')
    # Read the Excel file
    df = pd.read_excel(excel_file_path)

    # Replace NaN values with empty strings
    df = df.fillna('')

    # Drop unnamed columns (columns with no header)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    # Convert DataFrame to HTML
    data = df.to_html(classes='table table-striped', index=False)

    return render(request, 'preview/preview.html', {'data': data})



def main(request):
    reader, error_message = Shipment.open_checklist()
    data = None
    if reader:
        pass
    return render(request, 'main/main.html', {'error_message': error_message, 'data': data})


    shipment_list = Shipment.create_shipment()
    sum_collies = Shipment.calculate_total_collies(shipment_list)
    sum_weight = Shipment.calculate_total_weight(shipment_list)
    summary = f'Summe der Collies: {sum_collies} und Gewicht: {sum_weight}'

    return render(request, 'main/main.html', {
        'shipment_list': shipment_list,
        'summary': summary,
    })