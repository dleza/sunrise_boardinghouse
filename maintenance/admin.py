from django.contrib import admin
from .models import MaintenanceRequest

@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = ("reported_date", "room", "title", "status", "estimated_cost", "actual_cost")
    list_filter = ("status", "room")
    search_fields = ("title", "description", "room__name")
