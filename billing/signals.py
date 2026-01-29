from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum
from decimal import Decimal

from .models import RentPayment

def _recalc_invoice(invoice):
    total = invoice.payments.aggregate(s=Sum("amount"))["s"] or Decimal("0.00")
    invoice.amount_paid = total
    invoice.save(update_fields=["amount_paid"])
    invoice.update_status()

@receiver(post_save, sender=RentPayment)
def payment_saved(sender, instance, **kwargs):
    _recalc_invoice(instance.invoice)

@receiver(post_delete, sender=RentPayment)
def payment_deleted(sender, instance, **kwargs):
    _recalc_invoice(instance.invoice)
