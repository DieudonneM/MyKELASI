from django.db import IntegrityError, transaction
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import BasePermission
from rest_framework.response import Response

from accounts.roles import has_internal_role
from accounts.services import record_audit

from .admin_serializers import (
    ConfigurationVersionSerializer,
    LevelAdminSerializer,
    ServiceAreaAdminSerializer,
    SubjectAdminSerializer,
    TeachingModeAdminSerializer,
)
from .models import ConfigurationVersion, Level, ServiceArea, Subject, TeachingMode


class IsReferentialAdmin(BasePermission):
    def has_permission(self, request, view):
        return has_internal_role(request.user, "ADMIN", "SUPER_ADMIN")


REFERENTIALS = {
    "subjects": (Subject, SubjectAdminSerializer),
    "levels": (Level, LevelAdminSerializer),
    "teaching-modes": (TeachingMode, TeachingModeAdminSerializer),
    "service-areas": (ServiceArea, ServiceAreaAdminSerializer),
}


class ReferentialMixin:
    permission_classes = (IsReferentialAdmin,)

    def get_model_and_serializer(self):
        try:
            return REFERENTIALS[self.kwargs["kind"]]
        except KeyError as error:
            raise ValidationError({"kind": "Référentiel inconnu."}) from error

    def get_queryset(self):
        model, _ = self.get_model_and_serializer()
        return model.objects.all()

    def get_serializer_class(self):
        _, serializer_class = self.get_model_and_serializer()
        return serializer_class


class ReferentialListCreateAPIView(ReferentialMixin, generics.ListCreateAPIView):
    def list(self, request, *args, **kwargs):
        record_audit(actor=request.user, action="referential.list", target=request.user)
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        item = serializer.save()
        record_audit(actor=self.request.user, action="referential.create", target=item)


class ReferentialDetailAPIView(ReferentialMixin, generics.RetrieveUpdateDestroyAPIView):
    def perform_update(self, serializer):
        item = serializer.save()
        record_audit(actor=self.request.user, action="referential.update", target=item)

    def destroy(self, request, *args, **kwargs):
        item = self.get_object()
        if any(
            relation.related_model.objects.filter(**{relation.field.name: item}).exists()
            for relation in item._meta.related_objects
        ):
            return Response(
                {"detail": "Une référence utilisée ne peut pas être supprimée; désactivez-la."},
                status=status.HTTP_409_CONFLICT,
            )
        record_audit(actor=request.user, action="referential.delete", target=item)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ConfigurationVersionListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ConfigurationVersionSerializer
    permission_classes = (IsReferentialAdmin,)

    def get_queryset(self):
        return ConfigurationVersion.objects.all()

    @transaction.atomic
    def perform_create(self, serializer):
        key = serializer.validated_data["key"]
        latest = ConfigurationVersion.objects.select_for_update().filter(key=key).first()
        version = (latest.version if latest else 0) + 1
        try:
            item = serializer.save(created_by=self.request.user, version=version)
        except IntegrityError as error:
            raise ValidationError({"key": "Conflit de publication, réessayez."}) from error
        record_audit(actor=self.request.user, action="configuration.publish", target=item)
