import django
from django.conf import settings
import sys
import os

# wa_automater/ ins sys.path damit 'wa_automater.settings' gefunden wird
sys.path.insert(0, os.path.dirname(__file__))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wa_automater.settings')
django.setup()
