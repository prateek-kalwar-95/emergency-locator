from django.contrib import admin
from locator.models import ServiceUnit, Incident

@admin.register(ServiceUnit)
class ServiceUnitAdmin(admin.ModelAdmin):
    list_display = ('unit_id', 'unit_type', 'latitude', 'longitude', 'status')
    list_filter = ('unit_type', 'status')
    search_fields = ('unit_id',)

@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ('name', 'latitude', 'longitude', 'source', 'created_at')
    list_filter = ('source', 'created_at')
    search_fields = ('name',)
