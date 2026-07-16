# main/urls.py


from django.urls import path
from .views import main
from .views import main, download_excel


urlpatterns = [
    path('', main, name='main'),
    path('download/', download_excel, name='download_excel'),
]

