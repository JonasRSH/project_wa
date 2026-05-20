from django.shortcuts import render
import sys
import os
import pathlib


BASE_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR / 'Python_Back_End' / 'loading_list_check'))


def wa_automator(request):
    return render(request, 'main/main.html')