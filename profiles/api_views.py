from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.permissions import AllowAny

from .filters import TeacherSearchFilter
from .models import TeacherProfile
from .serializers import TeacherSearchSerializer


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
