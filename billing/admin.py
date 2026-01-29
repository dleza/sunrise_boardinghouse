from django.contrib import admin
from .models import BreakMonthSetting, RentInvoice, RentPayment

@admin.register(BreakMonthSetting)
class BreakMonthSettingAdmin(admin.ModelAdmin):
    list_display = ("month", "rent_multiplier")
    ordering = ("month",)

@admin.register(RentInvoice)
class RentInvoiceAdmin(admin.ModelAdmin):
    list_display = ("student", "due_date", "amount_due", "amount_paid", "status")
    list_filter = ("status",)
    search_fields = ("student__full_name", "occupancy__room__name")
    ordering = ("-due_date",)

@admin.register(RentPayment)
class RentPaymentAdmin(admin.ModelAdmin):
    list_display = ("invoice", "payment_date", "amount", "method", "reference")
    list_filter = ("method",)
    search_fields = ("invoice__student__full_name", "reference")
