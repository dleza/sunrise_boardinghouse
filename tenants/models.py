from django.db import models
from rooms.models import Room

class Student(models.Model):
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=30)
    guardian_name = models.CharField(max_length=200, blank=True)
    guardian_phone = models.CharField(max_length=30, blank=True)
    school = models.CharField(max_length=200, blank=True)
    national_id = models.CharField(max_length=60, blank=True)

    def __str__(self) -> str:
        return self.full_name


class Occupancy(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="occupancies")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="occupancies")
    entry_date = models.DateField()
    exit_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["active"]),
            models.Index(fields=["room", "active"]),
        ]

    def __str__(self) -> str:
        return f"{self.student} in {self.room}"

    @property
    def billing_day(self) -> int:
        return self.entry_date.day
