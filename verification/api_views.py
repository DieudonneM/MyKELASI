from pathlib import Path

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.roles import has_internal_role
from accounts.services import record_audit
from notifications.models import Notification

from .models import (
    IdentityVerification,
    ProfessionalCredential,
    VerificationDecision,
    VerificationStatus,
    VerificationUpload,
)
from .serializers_api import (
    VerificationDecisionSerializer,
    VerificationDocumentModelSerializer,
    VerificationReviewSerializer,
    VerificationUploadSerializer,
)


class IsTeacher(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated
            and request.user.is_active
            and request.user.status == "ACTIVE"
            and request.user.account_type == "TEACHER"
        )


class TeacherVerificationListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = (IsTeacher,)
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_queryset(self):
        return list(IdentityVerification.objects.filter(user=self.request.user)) + list(
            ProfessionalCredential.objects.filter(user=self.request.user)
        )

    def get_serializer_class(self):
        return (
            VerificationUploadSerializer
            if self.request.method == "POST"
            else VerificationDocumentModelSerializer
        )

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response({"results": serializer.data})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        document = data.pop("document")
        if "document_type" in data:
            item = IdentityVerification.objects.create(user=request.user, document=document, **data)
        else:
            item = ProfessionalCredential.objects.create(
                user=request.user, document=document, **data
            )
        output = VerificationDocumentModelSerializer(item)
        return Response(output.data, status=status.HTTP_201_CREATED)


class VerificationReviewAPIView(APIView):
    @transaction.atomic
    def post(self, request, kind, pk):
        if not has_internal_role(request.user, "VERIFICATION"):
            return Response({"detail": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)
        model = {
            "identity": IdentityVerification,
            "credential": ProfessionalCredential,
        }.get(kind)
        if model is None:
            return Response({"detail": "Type inconnu."}, status=status.HTTP_404_NOT_FOUND)
        serializer = VerificationReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = get_object_or_404(model.objects.select_for_update(), pk=pk)
        if item.status != VerificationStatus.PENDING:
            return Response(
                {"detail": "Ce document a déjà reçu une décision."},
                status=status.HTTP_409_CONFLICT,
            )
        new_status = serializer.validated_data["status"]
        reason = serializer.validated_data["rejection_reason"].strip()
        previous_status = item.status
        with transaction.atomic():
            item.status = new_status
            item.rejection_reason = reason
            item.reviewed_by = request.user
            item.reviewed_at = timezone.now()
            item.save(update_fields=("status", "rejection_reason", "reviewed_by", "reviewed_at"))
            VerificationDecision.objects.create(
                document_type=kind,
                document_id=item.pk,
                reviewer=request.user,
                from_status=previous_status,
                to_status=new_status,
                reason=reason,
            )
            record_audit(
                actor=request.user,
                action="verification.review",
                target=item,
                metadata={"from_status": previous_status, "to_status": new_status},
            )
            Notification.objects.create(
                user=item.user,
                kind=Notification.Kind.VERIFICATION_UPDATED,
                title="Vérification mise à jour",
                body=(
                    "Votre document a été approuvé."
                    if new_status == VerificationStatus.APPROVED
                    else (
                        "Votre document a été refusé. Consultez le motif et déposez "
                        "une nouvelle pièce."
                    )
                    if new_status == VerificationStatus.REJECTED
                    else (
                        "Votre document a expiré. Consultez le motif et déposez une nouvelle pièce."
                    )
                ),
            )
        return Response(VerificationDocumentModelSerializer(item).data)


class VerificationQueueAPIView(APIView):
    def get(self, request):
        if not has_internal_role(request.user, "VERIFICATION"):
            return Response({"detail": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)
        record_audit(actor=request.user, action="verification.queue_view", target=request.user)
        identity = IdentityVerification.objects.filter(
            status=VerificationStatus.PENDING
        ).select_related("user")
        credentials = ProfessionalCredential.objects.filter(
            status=VerificationStatus.PENDING
        ).select_related("user")
        results = [
            {"kind": "identity", **VerificationDocumentModelSerializer(item).data}
            for item in identity
        ] + [
            {"kind": "credential", **VerificationDocumentModelSerializer(item).data}
            for item in credentials
        ]
        return Response({"count": len(results), "results": results})


class VerificationDocumentAPIView(APIView):
    def get(self, request, kind, pk):
        if not has_internal_role(request.user, "VERIFICATION"):
            return Response({"detail": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)
        model = {"identity": IdentityVerification, "credential": ProfessionalCredential}.get(kind)
        if model is None:
            return Response({"detail": "Type inconnu."}, status=status.HTTP_404_NOT_FOUND)
        item = get_object_or_404(model, pk=pk)
        record_audit(actor=request.user, action="verification.document_view", target=item)
        response = FileResponse(item.document.open("rb"), as_attachment=True)
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        return response


class VerificationHistoryAPIView(APIView):
    def get(self, request, kind, pk):
        if not has_internal_role(request.user, "VERIFICATION"):
            return Response({"detail": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)
        model = {"identity": IdentityVerification, "credential": ProfessionalCredential}.get(kind)
        if model is None:
            return Response({"detail": "Type inconnu."}, status=status.HTTP_404_NOT_FOUND)
        get_object_or_404(model, pk=pk)
        history = VerificationDecision.objects.filter(
            document_type=kind, document_id=pk
        ).select_related("reviewer")
        record_audit(actor=request.user, action="verification.history_view", target=request.user)
        return Response({"results": VerificationDecisionSerializer(history, many=True).data})


class TeacherVerificationUploadAPIView(APIView):
    permission_classes = (IsTeacher,)
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def post(self, request):
        document_type = request.data.get("credential_type") or request.data.get("document_type")
        file_name = request.data.get("file_name", "")
        try:
            file_size = int(request.data.get("file_size", 0))
        except TypeError, ValueError:
            file_size = 0
        if not document_type or not file_name:
            return Response({"detail": "Type et nom de fichier obligatoires."}, status=400)
        if file_size <= 0 or file_size > 5 * 1024 * 1024:
            return Response({"detail": "Taille de fichier invalide."}, status=400)
        upload = VerificationUpload.objects.create(
            user=request.user,
            document_type=document_type,
            file_name=file_name,
            file_size=file_size,
            title=request.data.get("title", ""),
        )
        upload.chunk_file.save(upload.chunk_file.name, ContentFile(b""), save=True)
        return Response({"upload_id": str(upload.public_id), "offset": 0}, status=201)

    def get(self, request, upload_id):
        upload = get_object_or_404(VerificationUpload, public_id=upload_id, user=request.user)
        return Response({"upload_id": str(upload.public_id), "offset": upload.received_size})

    def patch(self, request, upload_id):
        upload = get_object_or_404(VerificationUpload, public_id=upload_id, user=request.user)
        chunk = request.FILES.get("chunk")
        try:
            offset = int(request.headers.get("Upload-Offset", "-1"))
        except ValueError:
            offset = -1
        if chunk is None or offset != upload.received_size:
            return Response({"offset": upload.received_size}, status=409)
        with upload.chunk_file.storage.open(upload.chunk_file.name, "ab") as target:
            for piece in chunk.chunks():
                target.write(piece)
        upload.received_size += chunk.size
        upload.save(update_fields=("received_size",))
        if upload.received_size < upload.file_size:
            return Response({"upload_id": str(upload.public_id), "offset": upload.received_size})
        if upload.received_size != upload.file_size:
            upload.delete()
            return Response({"detail": "Taille reçue invalide."}, status=400)
        with upload.chunk_file.storage.open(upload.chunk_file.name, "rb") as source:
            content = source.read()
        content_type = {
            ".pdf": "application/pdf",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
        }.get(Path(upload.file_name).suffix.lower())
        document = SimpleUploadedFile(upload.file_name, content, content_type=content_type)
        from .validators import validate_document

        try:
            validate_document(document)
        except DjangoValidationError as error:
            upload.delete()
            raise DRFValidationError(error.messages) from error
        if upload.document_type in ("DIPLOMA", "CERTIFICATE", "diploma", "certificate"):
            item = ProfessionalCredential.objects.create(
                user=request.user,
                credential_type=upload.document_type.upper(),
                title=upload.title,
                document=document,
            )
        else:
            item = IdentityVerification.objects.create(
                user=request.user,
                document_type=upload.document_type.upper(),
                document=document,
            )
        response = VerificationDocumentModelSerializer(item).data
        upload.delete()
        return Response(response, status=201)
