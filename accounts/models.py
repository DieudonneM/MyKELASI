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
