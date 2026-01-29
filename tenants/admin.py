from django.contrib import admin
from .models import Student, Occupancy

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone", "school")
    search_fields = ("full_name", "phone", "school")

@admin.register(Occupancy)
class OccupancyAdmin(admin.ModelAdmin):
    list_display = ("student", "room", "entry_date", "active")
    list_filter = ("active", "room")
    search_fields = ("student__full_name", "room__name")
