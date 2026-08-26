from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.permissions import AllowAny, BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import TeacherSearchFilter
from .models import Level, ServiceArea, Subject, TeacherProfile, TeachingMode
from .serializers import (
    AvailabilitySerializer,
    TeacherProfileReferenceSerializer,
    TeacherProfileSerializer,
    TeacherSearchSerializer,
)


class IsTeacher(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.account_type == "TEACHER")


class TeacherProfileAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = TeacherProfileSerializer
    permission_classes = (IsTeacher,)

    def get_object(self):
        profile, _ = TeacherProfile.objects.get_or_create(user=self.request.user)
        return profile


class TeacherProfileCatalogAPIView(APIView):
    permission_classes = (IsTeacher,)

    def get(self, request):
        serializer = TeacherProfileReferenceSerializer
        return Response(
            {
                "subjects": serializer(Subject.objects.filter(is_active=True), many=True).data,
                "levels": serializer(Level.objects.filter(is_active=True), many=True).data,
                "teaching_modes": serializer(
                    TeachingMode.objects.filter(is_active=True), many=True
                ).data,
                "service_areas": serializer(
                    ServiceArea.objects.filter(is_active=True), many=True
                ).data,
            }
        )


class TeacherAvailabilityListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = AvailabilitySerializer
    permission_classes = (IsTeacher,)

    def get_queryset(self):
        return self.request.user.teacher_profile.availabilities.all()

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user.teacher_profile)


class TeacherAvailabilityDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AvailabilitySerializer
    permission_classes = (IsTeacher,)

    def get_queryset(self):
        return self.request.user.teacher_profile.availabilities.all()


class TeacherSearchAPIView(generics.ListAPIView):
    serializer_class = TeacherSearchSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TeacherSearchFilter

    def get_queryset(self):
        return (
            TeacherProfile.objects.filter(
                is_public=True,
                user__is_active=True,
                subjects__is_active=True,
            )
            .select_related("user")
            .prefetch_related("subjects", "levels", "teaching_modes", "service_areas")
            .distinct()
        )
