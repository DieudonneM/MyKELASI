import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse

from learning.models import Proposal
from profiles.models import ServiceArea, TeachingMode


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "En attente"
        CONFIRMED = "CONFIRMED", "Confirmée"
        REJECTED = "REJECTED", "Refusée"
        CANCELLED = "CANCELLED", "Annulée"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    proposal = models.OneToOneField(
        Proposal,
        on_delete=models.PROTECT,
        related_name="booking",
    )
    learner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="learner_bookings",
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="teacher_bookings",
    )
    start_at = models.DateTimeField("début")
    end_at = models.DateTimeField("fin")
    teaching_mode = models.ForeignKey(TeachingMode, on_delete=models.PROTECT)
    service_area = models.ForeignKey(
        ServiceArea,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    currency = models.CharField(max_length=3, default="CDF", editable=False)
    cancellation_policy = models.TextField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("start_at",)
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_at__gt=models.F("start_at")),
                name="booking_end_after_start",
            )
        ]

    def __str__(self):
        return f"{self.proposal.learning_request.subject} - {self.start_at}"

    def get_absolute_url(self):
        return reverse("bookings:detail", kwargs={"public_id": self.public_id})


class BookingTransition(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="transitions")
    from_status = models.CharField(max_length=10, choices=Booking.Status.choices, blank=True)
    to_status = models.CharField(max_length=10, choices=Booking.Status.choices)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="booking_transitions",
    )
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)

    def __str__(self):
        return f"{self.booking.public_id}: {self.from_status} -> {self.to_status}"
