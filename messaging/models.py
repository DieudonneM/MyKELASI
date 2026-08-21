import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse

from bookings.models import Booking
from learning.models import LearningRequest, Proposal
from profiles.models import TeacherProfile
from reviews.models import Review


class Conversation(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    learning_request = models.ForeignKey(
        LearningRequest,
        on_delete=models.CASCADE,
        related_name="conversations",
    )
    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name="conversation",
        null=True,
        blank=True,
    )
    learner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="learner_conversations",
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="teacher_conversations",
    )
    last_message_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-last_message_at", "-created_at")
        constraints = [
            models.UniqueConstraint(
                fields=("learning_request", "learner", "teacher"),
                name="unique_request_participant_conversation",
            ),
            models.CheckConstraint(
                condition=~models.Q(learner=models.F("teacher")),
                name="conversation_distinct_participants",
            ),
        ]

    def __str__(self):
        return f"{self.learner} / {self.teacher}"

    def get_absolute_url(self):
        return reverse("messaging:detail", kwargs={"public_id": self.public_id})


class Message(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sent_messages",
    )
    content = models.TextField(max_length=4000)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)
        indexes = [
            models.Index(
                fields=("conversation", "created_at"),
                name="messaging_m_convers_2c54d4_idx",
            )
        ]

    def __str__(self):
        return f"{self.author} - {self.created_at}"


class Report(models.Model):
    class Reason(models.TextChoices):
        SPAM = "SPAM", "Spam"
        HARASSMENT = "HARASSMENT", "Harcèlement"
        FRAUD = "FRAUD", "Fraude"
        INAPPROPRIATE = "INAPPROPRIATE", "Contenu inapproprié"
        OTHER = "OTHER", "Autre"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Ouvert"
        IN_REVIEW = "IN_REVIEW", "En cours"
        RESOLVED = "RESOLVED", "Résolu"
        DISMISSED = "DISMISSED", "Classé"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reports",
    )
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="reports",
        null=True,
        blank=True,
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="reports",
        null=True,
        blank=True,
    )
    teacher_profile = models.ForeignKey(
        TeacherProfile,
        on_delete=models.CASCADE,
        related_name="reports",
        null=True,
        blank=True,
    )
    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.CASCADE,
        related_name="reports",
        null=True,
        blank=True,
    )
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="reports",
        null=True,
        blank=True,
    )
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name="reports",
        null=True,
        blank=True,
    )
    reason = models.CharField(max_length=20, choices=Reason.choices)
    description = models.TextField(max_length=2000, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(conversation__isnull=False)
                    | models.Q(teacher_profile__isnull=False)
                    | models.Q(proposal__isnull=False)
                    | models.Q(booking__isnull=False)
                    | models.Q(review__isnull=False)
                ),
                name="report_has_target",
            ),
            models.CheckConstraint(
                condition=~(
                    models.Q(conversation__isnull=False, teacher_profile__isnull=False)
                    | models.Q(conversation__isnull=False, proposal__isnull=False)
                    | models.Q(conversation__isnull=False, booking__isnull=False)
                    | models.Q(conversation__isnull=False, review__isnull=False)
                    | models.Q(teacher_profile__isnull=False, proposal__isnull=False)
                    | models.Q(teacher_profile__isnull=False, booking__isnull=False)
                    | models.Q(teacher_profile__isnull=False, review__isnull=False)
                    | models.Q(proposal__isnull=False, booking__isnull=False)
                    | models.Q(proposal__isnull=False, review__isnull=False)
                    | models.Q(booking__isnull=False, review__isnull=False)
                ),
                name="report_has_single_target",
            ),
            models.CheckConstraint(
                condition=models.Q(message__isnull=True)
                | models.Q(conversation__isnull=False),
                name="report_message_requires_conversation",
            ),
        ]

    @property
    def target_label(self):
        if self.message_id:
            return "Message"
        if self.conversation_id:
            return "Conversation"
        if self.teacher_profile_id:
            return "Profil enseignant"
        if self.proposal_id:
            return "Proposition"
        if self.review_id:
            return "Avis"
        return "Réservation"


class ReportAction(models.Model):
    class Action(models.TextChoices):
        VIEWED = "VIEWED", "Consulté"
        IN_REVIEW = "IN_REVIEW", "Pris en charge"
        RESOLVED = "RESOLVED", "Résolu"
        DISMISSED = "DISMISSED", "Classé"

    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="actions")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="report_actions",
    )
    action = models.CharField(max_length=12, choices=Action.choices)
    note = models.TextField(max_length=2000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)
