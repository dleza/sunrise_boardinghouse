from django.db import models
from rooms.models import Room
from decimal import Decimal
from django.core.exceptions import ValidationError


class Area(models.Model):
    name = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.name

class MaintenanceRequest(models.Model):
    STATUS = [
        ("OPEN", "Open"),
        ("IN_PROGRESS", "In Progress"),
        ("DONE", "Done"),
    ]

    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name="maintenance_requests")
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True, related_name="maintenance_requests")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=STATUS, default="OPEN")

    reported_date = models.DateField()
    resolved_date = models.DateField(null=True, blank=True)

    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    actual_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-reported_date", "-created_at"]

    def __str__(self):
        return f"{self.room.name} - {self.title} ({self.status})"


def clean(self):
    if not self.room and not self.area:
        raise ValidationError("Select either a Room or an Area (e.g. Kitchen/Shower).")
    if self.room and self.area:
        raise ValidationError("Select only one: Room OR Area (not both).")
