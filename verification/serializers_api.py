from pathlib import Path

from rest_framework import serializers

from .models import IdentityVerification, ProfessionalCredential, VerificationStatus
from .validators import validate_document


class VerificationDocumentSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    document_type = serializers.CharField(read_only=True)
    credential_type = serializers.CharField(read_only=True, allow_null=True)
    title = serializers.CharField(read_only=True, allow_null=True)
    file_name = serializers.CharField(read_only=True)
    status = serializers.SerializerMethodField()
    uploaded_at = serializers.DateTimeField(source="created_at", read_only=True)
    reviewed_at = serializers.DateTimeField(read_only=True)
    rejection_reason = serializers.CharField(read_only=True, allow_blank=True)

    def get_status(self, obj):
        return obj.status.lower()


class VerificationUploadSerializer(serializers.Serializer):
    document_type = serializers.ChoiceField(
        choices=(
            (IdentityVerification.DocumentType.NATIONAL_ID, "Carte d'identité"),
            (IdentityVerification.DocumentType.PASSPORT, "Passeport"),
            (IdentityVerification.DocumentType.VOTER_CARD, "Carte d'électeur"),
            (IdentityVerification.DocumentType.DRIVING_LICENSE, "Permis de conduire"),
            ("identity_card", "Carte d'identité"),
            ("residence_permit", "Permis de séjour"),
            ("passport", "Passeport"),
            ("diploma", "Diplôme"),
            ("certificate", "Certificat"),
        ),
        required=False,
    )
    credential_type = serializers.ChoiceField(
        choices=ProfessionalCredential.CredentialType.choices,
        required=False,
    )
    title = serializers.CharField(max_length=180, required=False, allow_blank=True)
    institution = serializers.CharField(max_length=180, required=False, allow_blank=True)
    issued_year = serializers.IntegerField(required=False, min_value=1900, max_value=2200)
    document = serializers.FileField()

    def validate(self, attrs):
        aliases = {
            "identity_card": IdentityVerification.DocumentType.NATIONAL_ID,
            "residence_permit": IdentityVerification.DocumentType.NATIONAL_ID,
            "passport": IdentityVerification.DocumentType.PASSPORT,
            "diploma": ProfessionalCredential.CredentialType.DIPLOMA,
            "certificate": ProfessionalCredential.CredentialType.CERTIFICATE,
        }
        document_type = attrs.get("document_type")
        if document_type in ("diploma", "certificate"):
            attrs["credential_type"] = aliases[document_type]
            attrs.pop("document_type")
        elif document_type in aliases:
            attrs["document_type"] = aliases[document_type]
        has_identity = bool(attrs.get("document_type"))
        has_credential = bool(attrs.get("credential_type"))
        if has_identity == has_credential:
            raise serializers.ValidationError(
                "Choisissez un document d'identité ou une certification professionnelle."
            )
        if has_credential and not attrs.get("title", "").strip():
            raise serializers.ValidationError({"title": "Le titre est obligatoire."})
        validate_document(attrs["document"])
        return attrs


class VerificationReviewSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=(
            (VerificationStatus.APPROVED, "Approuvé"),
            (VerificationStatus.REJECTED, "Refusé"),
            (VerificationStatus.EXPIRED, "Expiré"),
        )
    )
    rejection_reason = serializers.CharField(required=False, allow_blank=True, max_length=2000)

    def validate(self, attrs):
        if (
            attrs["status"] == VerificationStatus.REJECTED
            and not attrs.get("rejection_reason", "").strip()
        ):
            raise serializers.ValidationError(
                {"rejection_reason": "Le motif est obligatoire pour un rejet."}
            )
        return attrs


class VerificationDocumentModelSerializer(VerificationDocumentSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if isinstance(instance, ProfessionalCredential):
            data["document_type"] = instance.credential_type.lower()
            data["credential_type"] = instance.credential_type.lower()
            data["title"] = instance.title
        else:
            data["document_type"] = instance.document_type.lower()
            data["credential_type"] = None
            data["title"] = None
        data["file_name"] = Path(instance.document.name).name
        return data
