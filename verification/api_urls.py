from django.urls import path

from .api_views import (
    TeacherVerificationListCreateAPIView,
    TeacherVerificationUploadAPIView,
    VerificationReviewAPIView,
)

urlpatterns = [
    path(
        "teacher/verifications/",
        TeacherVerificationListCreateAPIView.as_view(),
        name="teacher-verifications",
    ),
    path(
        "verification/<str:kind>/<int:pk>/review/",
        VerificationReviewAPIView.as_view(),
        name="verification-review",
    ),
    path(
        "teacher/verifications/upload/",
        TeacherVerificationUploadAPIView.as_view(),
        name="teacher-verification-upload",
    ),
    path(
        "teacher/verifications/upload/<uuid:upload_id>/",
        TeacherVerificationUploadAPIView.as_view(),
        name="teacher-verification-upload-chunk",
    ),
]