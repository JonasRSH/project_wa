from django.shortcuts import render
import sys
import os
from Python_Back_End.loading_list_check.CustomsList import Shipment
from t1_reader import data_filter
import pathlib


BASE_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR / 'Python_Back_End' / 'loading_list_check'))
sys.path.append(str(BASE_DIR / 'Python_Back_End' / 't1_reader'))


def wa_automator(request):
    return render(request, 'main/main.html')