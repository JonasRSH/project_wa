from django.shortcuts import render
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from Python_Back_End.loading_list_check.CustomsList import Shipment

def wa_automator(request):
    return render(request, 'main/main.html')