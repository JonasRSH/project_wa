# main/urls.py


from django.urls import path
from .views import main, download_excel, clear_uploaded_data


urlpatterns = [
    path('', main, name='main'),
    path('download/', download_excel, name='download_excel'),
    path('clear-data/', clear_uploaded_data, name='clear_uploaded_data'),
]

