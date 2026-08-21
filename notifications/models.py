from django.conf import settings
from django.db import models

from bookings.models import Booking


class Notification(models.Model):
    class Kind(models.TextChoices):
        SESSION_REMINDER_24H = "SESSION_REMINDER_24H", "Rappel de session 24 h"
        SESSION_REMINDER_1H = "SESSION_REMINDER_1H", "Rappel de session 1 h"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    kind = models.CharField(max_length=24, choices=Kind.choices)
    title = models.CharField(max_length=180)
    body = models.TextField()
    emailed_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("user", "booking", "kind"),
                name="unique_booking_reminder_per_user",
            )
        ]

    def __str__(self):
        return f"{self.user}: {self.title}"
