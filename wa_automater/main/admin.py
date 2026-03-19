from django.contrib import admin
from .models import Abfahrt, Zollamt


class AbfahrtAdmin(admin.ModelAdmin):
    list_display = ('name', 'kennzeichen', 'anhaenger', 'created_by')
    list_filter = ('created_by',)
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nur beim Erstellen
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(created_by=request.user)


class ZollamtAdmin(admin.ModelAdmin):
    list_display = ('name', 'typ', 'created_by')
    list_filter = ('typ', 'created_by')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nur beim Erstellen
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(created_by=request.user)


admin.site.register(Abfahrt, AbfahrtAdmin)
admin.site.register(Zollamt, ZollamtAdmin)
