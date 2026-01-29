from django.db import models
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date

from tenants.models import Student, Occupancy

class BreakMonthSetting(models.Model):
    """
    Global break-month rule. You chose:
    June = 50%, December = 50%
    """
    month = models.PositiveSmallIntegerField(unique=True)  # 1-12
    rent_multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("1.00"))

    def clean(self):
        if not (1 <= self.month <= 12):
            raise ValidationError("month must be between 1 and 12.")
        if self.rent_multiplier <= 0:
            raise ValidationError("rent_multiplier must be > 0.")

    def __str__(self):
        return f"Month {self.month}: x{self.rent_multiplier}"


class RentInvoice(models.Model):
    STATUS = [
        ("UNPAID", "Unpaid"),
        ("PARTIAL", "Partial"),
        ("PAID", "Paid"),
        ("OVERDUE", "Overdue"),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="invoices")
    occupancy = models.ForeignKey(Occupancy, on_delete=models.CASCADE, related_name="invoices")

    due_date = models.DateField()
    period_start = models.DateField()
    period_end = models.DateField()

    amount_due = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(max_length=10, choices=STATUS, default="UNPAID")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-due_date"]
        constraints = [
            models.UniqueConstraint(fields=["occupancy", "due_date"], name="uniq_occupancy_due_date")
        ]

    def __str__(self):
        return f"{self.student} - {self.due_date} - {self.status}"

    @property
    def balance(self) -> Decimal:
        return (self.amount_due - self.amount_paid)

    def update_status(self):
        today = date.today()
        if self.amount_paid >= self.amount_due:
            self.status = "PAID"
        elif self.amount_paid > 0:
            self.status = "PARTIAL"
        elif today > self.due_date:
            self.status = "OVERDUE"
        else:
            self.status = "UNPAID"
        self.save(update_fields=["status"])


class RentPayment(models.Model):
    METHOD = [
        ("MOBILE_MONEY", "Mobile Money"),
        ("OTHER", "Other"),
    ]

    invoice = models.ForeignKey(RentInvoice, on_delete=models.CASCADE, related_name="payments")
    payment_date = models.DateField(auto_now_add=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=20, choices=METHOD, default="MOBILE_MONEY")
    reference = models.CharField(max_length=120, blank=True)

    def __str__(self):
        return f"{self.invoice.student} paid {self.amount} on {self.payment_date}"

    def clean(self):
        if self.amount <= 0:
            raise ValidationError("Payment amount must be > 0.")
