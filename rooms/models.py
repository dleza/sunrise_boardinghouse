from django.db import models
from django.core.exceptions import ValidationError
from datetime import timedelta

class Room(models.Model):
    name = models.CharField(max_length=120, unique=True)
    capacity = models.PositiveIntegerField()
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name

    def active_price(self):
        return self.prices.filter(end_date__isnull=True).order_by("-start_date").first()

    def price_for_date(self, dt):
        # price record whose start_date <= dt and (end_date is null or end_date >= dt)
        return self.prices.filter(start_date__lte=dt).filter(
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=dt)
        ).order_by("-start_date").first()


class RoomPrice(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="prices")
    price = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-start_date"]
        constraints = [
            models.UniqueConstraint(fields=["room", "start_date"], name="uniq_room_start_date")
        ]

    def __str__(self) -> str:
        return f"{self.room.name} - {self.price} from {self.start_date}"

    def clean(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError("end_date cannot be earlier than start_date.")

    def save(self, *args, **kwargs):
        """
        Start-date pricing rule (Option A):
        When saving a NEW active price (end_date empty), automatically close the
        previously active price by setting its end_date = new.start_date - 1 day.
        """
        creating = self.pk is None

        if creating:
            # Find existing active price
            current = RoomPrice.objects.filter(room=self.room, end_date__isnull=True).order_by("-start_date").first()
            if current:
                if self.start_date <= current.start_date:
                    raise ValidationError(
                        "New price start_date must be after the current active price start_date."
                    )
                current.end_date = self.start_date - timedelta(days=1)
                current.save()

        super().save(*args, **kwargs)
