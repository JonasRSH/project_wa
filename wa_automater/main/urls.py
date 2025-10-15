# main/urls.py


from django.urls import path
from .views import main, settings_view

urlpatterns = [
    path('', main, name='main'),
    path('settings/', settings_view, name='settings'),
]
