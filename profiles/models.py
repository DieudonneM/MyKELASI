import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse


class Subject(models.Model):
    name = models.CharField("nom", max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField("actif", default=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "matière"
        verbose_name_plural = "matières"

    def __str__(self):
        return self.name


class Level(models.Model):
    name = models.CharField("nom", max_length=100, unique=True)
    code = models.SlugField(unique=True)
    order = models.PositiveSmallIntegerField("ordre", default=0)
    is_active = models.BooleanField("actif", default=True)

    class Meta:
        ordering = ("order", "name")
        verbose_name = "niveau"

    def __str__(self):
        return self.name


class TeachingMode(models.Model):
    name = models.CharField("nom", max_length=100, unique=True)
    code = models.SlugField(unique=True)
    is_active = models.BooleanField("actif", default=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "mode d'enseignement"

    def __str__(self):
        return self.name


class ServiceArea(models.Model):
    name = models.CharField("commune", max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField("actif", default=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "zone d'intervention"

    def __str__(self):
        return self.name


class LearnerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="learner_profile",
    )
    levels = models.ManyToManyField(Level, blank=True, related_name="learners")
    interests = models.ManyToManyField(Subject, blank=True, related_name="interested_learners")
    preferred_service_area = models.ForeignKey(
        ServiceArea,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="learners",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("user__email",)
        verbose_name = "profil apprenant"

    def __str__(self):
        return self.user.get_full_name() or self.user.email

    @property
    def completion_percentage(self):
        checks = (
            bool(self.user.first_name and self.user.last_name),
            self.levels.exists(),
            self.interests.exists(),
            self.preferred_service_area_id is not None,
        )
        return round(sum(checks) / len(checks) * 100)


class TeacherProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="teacher_profile",
    )
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    headline = models.CharField("titre professionnel", max_length=160, blank=True)
    bio = models.TextField("présentation", max_length=2000, blank=True)
    years_experience = models.PositiveSmallIntegerField(
        "années d'expérience",
        default=0,
        validators=[MaxValueValidator(80)],
    )
    hourly_rate = models.DecimalField(
        "tarif horaire",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    currency = models.CharField("devise", max_length=3, default="CDF", editable=False)
    languages = models.CharField("langues", max_length=250, blank=True)
    subjects = models.ManyToManyField(Subject, blank=True, related_name="teachers")
    levels = models.ManyToManyField(Level, blank=True, related_name="teachers")
    teaching_modes = models.ManyToManyField(TeachingMode, blank=True, related_name="teachers")
    service_areas = models.ManyToManyField(ServiceArea, blank=True, related_name="teachers")
    is_public = models.BooleanField("profil public", default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("user__first_name", "user__last_name", "user__email")
        verbose_name = "profil enseignant"

    def __str__(self):
        return self.user.get_full_name() or self.user.email

    def get_absolute_url(self):
        return reverse("profiles:teacher-detail", kwargs={"public_id": self.public_id})

    @property
    def completion_percentage(self):
        checks = (
            bool(self.user.first_name and self.user.last_name),
            bool(self.headline),
            bool(self.bio),
            self.hourly_rate is not None,
            self.subjects.exists(),
            self.levels.exists(),
            self.teaching_modes.exists(),
            self.service_areas.exists(),
        )
        return round(sum(checks) / len(checks) * 100)

    @property
    def can_publish(self):
        return self.completion_percentage == 100 and self.user.email_verified


class Availability(models.Model):
    class Weekday(models.IntegerChoices):
        MONDAY = 1, "Lundi"
        TUESDAY = 2, "Mardi"
        WEDNESDAY = 3, "Mercredi"
        THURSDAY = 4, "Jeudi"
        FRIDAY = 5, "Vendredi"
        SATURDAY = 6, "Samedi"
        SUNDAY = 7, "Dimanche"

    teacher = models.ForeignKey(
        TeacherProfile,
        on_delete=models.CASCADE,
        related_name="availabilities",
    )
    weekday = models.PositiveSmallIntegerField("jour", choices=Weekday.choices)
    start_time = models.TimeField("début")
    end_time = models.TimeField("fin")

    class Meta:
        ordering = ("weekday", "start_time")
        constraints = [
            models.UniqueConstraint(
                fields=("teacher", "weekday", "start_time", "end_time"),
                name="unique_teacher_availability",
            ),
            models.CheckConstraint(
                condition=models.Q(end_time__gt=models.F("start_time")),
                name="availability_end_after_start",
            ),
        ]

    def __str__(self):
        return f"{self.teacher} - {self.get_weekday_display()}"
