from django.contrib import admin

from .models import Abfahrt, Zollamt, TransitDocument, Customs, Shipment, Colli

admin.site.register(Abfahrt)
admin.site.register(Zollamt)
admin.site.register(TransitDocument)
admin.site.register(Customs)
admin.site.register(Shipment)
admin.site.register(Colli)
