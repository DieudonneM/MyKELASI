from django.urls import path

from .api_views import (
    PublicTeacherReviewListAPIView,
    ReviewCreateAPIView,
    ReviewReplyCreateAPIView,
    TeacherReputationAPIView,
    TeacherReviewListAPIView,
)

app_name = "reviews-api"

urlpatterns = [
    path("teachers/<uuid:teacher_id>/reviews/", PublicTeacherReviewListAPIView.as_view(), name="list"),
    path("bookings/<uuid:booking_id>/reviews/", ReviewCreateAPIView.as_view(), name="create"),
    path("teacher/reviews/", TeacherReviewListAPIView.as_view(), name="teacher-list"),
    path("teacher/reputation/", TeacherReputationAPIView.as_view(), name="teacher-reputation"),
    path("reviews/<uuid:review_id>/reply/", ReviewReplyCreateAPIView.as_view(), name="reply"),
]
