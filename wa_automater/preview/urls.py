# preview/urls.py

from django.urls import path
from .views import preview_excel

urlpatterns = [
    path('', preview_excel, name='preview_excel'),
]
