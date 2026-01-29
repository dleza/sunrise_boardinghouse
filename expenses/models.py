from django.db import models
from decimal import Decimal

class Expense(models.Model):
    CATEGORY = [
        ("CARETAKER", "Caretaker Salary"),
        ("ELECTRICITY", "Electricity"),
        ("TRASH", "Trash Collection"),
        ("REPAIRS", "Repairs"),
        ("OTHER", "Other"),
    ]

    category = models.CharField(max_length=20, choices=CATEGORY)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    expense_date = models.DateField()
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-expense_date", "-created_at"]

    def __str__(self):
        return f"{self.get_category_display()} - {self.amount} ({self.expense_date})"
