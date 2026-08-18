import uuid

from django.conf import settings
from django.db import models

from .validators import validate_document


def private_document_path(instance, filename):
    extension = filename.rsplit(".", 1)[-1].lower()
    return f"verification/{instance.user_id}/{uuid.uuid4()}.{extension}"


class VerificationStatus(models.TextChoices):
    PENDING = "PENDING", "En attente"
    APPROVED = "APPROVED", "Approuvé"
    REJECTED = "REJECTED", "Refusé"
    EXPIRED = "EXPIRED", "Expiré"


class IdentityVerification(models.Model):
    class DocumentType(models.TextChoices):
        NATIONAL_ID = "NATIONAL_ID", "Carte d'identité"
        PASSPORT = "PASSPORT", "Passeport"
        VOTER_CARD = "VOTER_CARD", "Carte d'électeur"
        DRIVING_LICENSE = "DRIVING_LICENSE", "Permis de conduire"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="identity_verifications",
    )
    document_type = models.CharField(max_length=20, choices=DocumentType.choices)
    document = models.FileField(upload_to=private_document_path, validators=[validate_document])
    status = models.CharField(
        max_length=10,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
    )
    rejection_reason = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_identity_verifications",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)


class ProfessionalCredential(models.Model):
    class CredentialType(models.TextChoices):
        DIPLOMA = "DIPLOMA", "Diplôme"
        ACADEMIC_RECORD = "ACADEMIC_RECORD", "Relevé ou attestation académique"
        CERTIFICATE = "CERTIFICATE", "Certificat professionnel"
        EXPERIENCE = "EXPERIENCE", "Attestation d'expérience"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="professional_credentials",
    )
    credential_type = models.CharField(max_length=20, choices=CredentialType.choices)
    title = models.CharField(max_length=180)
    institution = models.CharField(max_length=180, blank=True)
    issued_year = models.PositiveSmallIntegerField(null=True, blank=True)
    document = models.FileField(upload_to=private_document_path, validators=[validate_document])
    status = models.CharField(
        max_length=10,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
    )
    rejection_reason = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_professional_credentials",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
