import uuid

from django.conf import settings
from django.db import models

from .validators import validate_document


def private_document_path(instance, filename):
    extension = filename.rsplit(".", 1)[-1].lower()
    return f"verification/{instance.user_id}/{uuid.uuid4()}.{extension}"


def upload_chunk_path(instance, filename):
    return f"verification/{instance.user_id}/uploads/{instance.public_id}.part"


class VerificationStatus(models.TextChoices):
    PENDING = "PENDING", "En attente"
    APPROVED = "APPROVED", "Approuvé"
    REJECTED = "REJECTED", "Refusé"
    EXPIRED = "EXPIRED", "Expiré"


class VerificationUpload(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    document_type = models.CharField(max_length=20)
    title = models.CharField(max_length=180, blank=True)
    institution = models.CharField(max_length=180, blank=True)
    issued_year = models.PositiveSmallIntegerField(null=True, blank=True)
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    received_size = models.PositiveIntegerField(default=0)
    chunk_file = models.FileField(upload_to=upload_chunk_path)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)


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


class VerificationDecision(models.Model):
    document_type = models.CharField(max_length=20)
    document_id = models.PositiveBigIntegerField()
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="verification_decisions",
    )
    from_status = models.CharField(max_length=10, blank=True)
    to_status = models.CharField(max_length=10)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at", "pk")

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError("Une décision de vérification est immuable.")
        return super().save(*args, **kwargs)
