from django.urls import path

from .api_views import (
    TeacherAvailabilityDetailAPIView,
    TeacherAvailabilityListCreateAPIView,
    TeacherProfileAPIView,
    TeacherProfileCatalogAPIView,
)

app_name = "profiles-teacher-api"

urlpatterns = [
    path("teacher/profile/", TeacherProfileAPIView.as_view(), name="teacher-profile"),
    path(
        "teacher/profile/catalog/",
        TeacherProfileCatalogAPIView.as_view(),
        name="teacher-profile-catalog",
    ),
    path(
        "teacher/availabilities/",
        TeacherAvailabilityListCreateAPIView.as_view(),
        name="teacher-availabilities",
    ),
    path(
        "teacher/availabilities/<int:pk>/",
        TeacherAvailabilityDetailAPIView.as_view(),
        name="teacher-availability-detail",
    ),
]
