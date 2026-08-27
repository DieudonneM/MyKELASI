from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


class User(AbstractUser):
    class AccountType(models.TextChoices):
        LEARNER = "LEARNER", "Apprenant"
        TEACHER = "TEACHER", "Enseignant"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Actif"
        SUSPENDED = "SUSPENDED", "Suspendu"
        DEACTIVATED = "DEACTIVATED", "Désactivé"

    username = None
    email = models.EmailField("adresse email", unique=True)
    email_verified = models.BooleanField("email vérifié", default=False)
    phone_number = models.CharField("téléphone", max_length=20, unique=True, null=True, blank=True)
    phone_verified = models.BooleanField("téléphone vérifié", default=False)
    account_type = models.CharField(
        "type de compte",
        max_length=10,
        choices=AccountType.choices,
        blank=True,
    )
    status = models.CharField(
        "statut",
        max_length=12,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    is_internal = models.BooleanField("compte interne", default=False)
    created_at = models.DateTimeField("créé le", auto_now_add=True)
    updated_at = models.DateTimeField("modifié le", auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = "utilisateur"
        verbose_name_plural = "utilisateurs"
        ordering = ("email",)

    def __str__(self):
        return self.email


class AuditLog(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=80)
    target_type = models.CharField(max_length=80)
    target_id = models.CharField(max_length=80)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-pk")
        permissions = (("view_sensitive_auditlog", "Consulter les audits sensibles"),)

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError("Un journal d'audit est immuable.")
        return super().save(*args, **kwargs)
