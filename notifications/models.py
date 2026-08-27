from django.conf import settings
from django.db import models

from bookings.models import Booking
from learning.models import LearningRequest, Proposal


class Notification(models.Model):
    class Kind(models.TextChoices):
        EMAIL_VERIFICATION = "EMAIL_VERIFICATION", "Vérification email"
        MATCH_CREATED = "MATCH_CREATED", "Nouveau match"
        PROPOSAL_CREATED = "PROPOSAL_CREATED", "Nouvelle proposition"
        SESSION_REMINDER_24H = "SESSION_REMINDER_24H", "Rappel de session 24 h"
        SESSION_REMINDER_1H = "SESSION_REMINDER_1H", "Rappel de session 1 h"
        PROPOSAL_ACCEPTED = "PROPOSAL_ACCEPTED", "Proposition acceptée"
        PROPOSAL_REJECTED = "PROPOSAL_REJECTED", "Proposition refusée"
        BOOKING_CREATED = "BOOKING_CREATED", "Réservation créée"
        PAYMENT_COMPLETED = "PAYMENT_COMPLETED", "Paiement confirmé"
        SESSION_COMPLETED = "SESSION_COMPLETED", "Session terminée"
        REVIEW_REQUESTED = "REVIEW_REQUESTED", "Avis à publier"
        REVIEW_CREATED = "REVIEW_CREATED", "Nouvel avis"
        VERIFICATION_UPDATED = "VERIFICATION_UPDATED", "Vérification mise à jour"
        MODERATION_UPDATED = "MODERATION_UPDATED", "Modération mise à jour"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )
    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )
    learning_request = models.ForeignKey(
        LearningRequest,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )
    kind = models.CharField(max_length=32, choices=Kind.choices)
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


class NotificationPreference(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )
    email = models.BooleanField(default=True)
    push = models.BooleanField(default=True)
    sms = models.BooleanField(default=False)
    booking_reminders = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
