import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse

from profiles.models import Level, ServiceArea, Subject, TeacherProfile, TeachingMode


class LearningRequest(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Ouverte"
        MATCHED = "MATCHED", "Correspondances trouvées"
        CLOSED = "CLOSED", "Fermée"

    class Frequency(models.TextChoices):
        ONCE = "ONCE", "Une fois"
        WEEKLY = "WEEKLY", "Chaque semaine"
        INTENSIVE = "INTENSIVE", "Programme intensif"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    learner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="learning_requests",
    )
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="requests")
    level = models.ForeignKey(Level, on_delete=models.PROTECT, related_name="requests")
    teaching_mode = models.ForeignKey(
        TeachingMode,
        on_delete=models.PROTECT,
        related_name="requests",
    )
    service_area = models.ForeignKey(
        ServiceArea,
        on_delete=models.PROTECT,
        related_name="requests",
        null=True,
        blank=True,
    )
    budget_max = models.DecimalField(
        "budget maximal",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    preferred_date = models.DateField("date souhaitée", null=True, blank=True)
    preferred_start_time = models.TimeField("heure souhaitée", null=True, blank=True)
    frequency = models.CharField(max_length=10, choices=Frequency.choices, default=Frequency.ONCE)
    description = models.TextField("besoin", max_length=2000)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.subject} - {self.learner}"

    def get_absolute_url(self):
        return reverse("learning:request-detail", kwargs={"public_id": self.public_id})


class MatchResult(models.Model):
    learning_request = models.ForeignKey(
        LearningRequest,
        on_delete=models.CASCADE,
        related_name="matches",
    )
    teacher = models.ForeignKey(
        TeacherProfile,
        on_delete=models.CASCADE,
        related_name="matches",
    )
    score = models.PositiveSmallIntegerField()
    reasons = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-score", "teacher__user__first_name")
        constraints = [
            models.UniqueConstraint(
                fields=("learning_request", "teacher"),
                name="unique_request_teacher_match",
            )
        ]


class Proposal(models.Model):
    class Status(models.TextChoices):
        SENT = "SENT", "Envoyée"
        ACCEPTED = "ACCEPTED", "Acceptée"
        REJECTED = "REJECTED", "Refusée"
        WITHDRAWN = "WITHDRAWN", "Retirée"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    learning_request = models.ForeignKey(
        LearningRequest,
        on_delete=models.CASCADE,
        related_name="proposals",
    )
    teacher = models.ForeignKey(
        TeacherProfile,
        on_delete=models.CASCADE,
        related_name="proposals",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    message = models.TextField(max_length=1500)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.SENT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("learning_request", "teacher"),
                name="unique_teacher_proposal_per_request",
            )
        ]

    def __str__(self):
        return f"{self.teacher} - {self.learning_request}"


class LearningEvent(models.Model):
    class Name(models.TextChoices):
        REQUEST_CREATED = "request.created", "Demande créée"
        MATCH_CREATED = "match.created", "Matching créé"
        PROPOSAL_SENT = "proposal.sent", "Proposition envoyée"
        BOOKING_CREATED = "booking.created", "Réservation créée"
        SESSION_COMPLETED = "session.completed", "Session terminée"
        REVIEW_CREATED = "review.created", "Avis créé"
        PAYMENT_COMPLETED = "payment.completed", "Paiement terminé"

    name = models.CharField(max_length=30, choices=Name.choices)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="learning_events",
    )
    learning_request = models.ForeignKey(
        LearningRequest,
        on_delete=models.CASCADE,
        related_name="events",
    )
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
