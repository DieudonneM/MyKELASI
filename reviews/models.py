import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from bookings.models import Session
from profiles.models import TeacherProfile


class Review(models.Model):
    class Status(models.TextChoices):
        PUBLISHED = "PUBLISHED", "Publié"
        HIDDEN = "HIDDEN", "Masqué"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    session = models.ForeignKey(Session, on_delete=models.PROTECT, related_name="reviews")
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="authored_reviews",
    )
    subject = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="received_reviews",
    )
    rating = models.PositiveSmallIntegerField(
        validators=(MinValueValidator(1), MaxValueValidator(5))
    )
    punctuality = models.PositiveSmallIntegerField(
        validators=(MinValueValidator(1), MaxValueValidator(5))
    )
    communication = models.PositiveSmallIntegerField(
        validators=(MinValueValidator(1), MaxValueValidator(5))
    )
    quality = models.PositiveSmallIntegerField(
        validators=(MinValueValidator(1), MaxValueValidator(5))
    )
    comment = models.TextField(max_length=2000, blank=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PUBLISHED,
    )
    moderation_reason = models.TextField(max_length=2000, blank=True)
    moderated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="moderated_reviews",
        null=True,
        blank=True,
    )
    moderated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("session", "reviewer"),
                name="unique_reviewer_per_session",
            ),
            models.CheckConstraint(
                condition=~models.Q(reviewer=models.F("subject")),
                name="review_distinct_participants",
            ),
        ]

    def __str__(self):
        return f"{self.reviewer} → {self.subject}: {self.rating}/5"


class ReviewResponse(models.Model):
    review = models.OneToOneField(Review, on_delete=models.CASCADE, related_name="response")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="review_responses",
    )
    content = models.TextField(max_length=2000)
    is_hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class ReviewModerationAction(models.Model):
    class Action(models.TextChoices):
        HIDDEN = "HIDDEN", "Masqué"
        RESTORED = "RESTORED", "Restauré"

    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="moderation_actions")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="review_moderation_actions",
    )
    action = models.CharField(max_length=10, choices=Action.choices)
    reason = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)


class TrustScoreSnapshot(models.Model):
    teacher_profile = models.ForeignKey(
        TeacherProfile,
        on_delete=models.CASCADE,
        related_name="trust_score_snapshots",
    )
    version = models.CharField(max_length=20)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    components = models.JSONField(default=dict)
    input_counts = models.JSONField(default=dict)
    source = models.CharField(max_length=40)
    calculated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-calculated_at", "-pk")
