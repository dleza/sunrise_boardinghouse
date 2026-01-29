from django.contrib import admin
from .models import Room, RoomPrice

class RoomPriceInline(admin.TabularInline):
    model = RoomPrice
    extra = 1

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("name", "capacity")
    search_fields = ("name",)
    inlines = [RoomPriceInline]

@admin.register(RoomPrice)
class RoomPriceAdmin(admin.ModelAdmin):
    list_display = ("room", "price", "start_date", "end_date")
    list_filter = ("room",)
    ordering = ("-start_date",)
