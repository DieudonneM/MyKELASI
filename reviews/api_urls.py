from django.urls import path

from .api_views import ReviewCreateAPIView, TeacherReviewListAPIView

app_name = "reviews-api"

urlpatterns = [
    path("teachers/<uuid:teacher_id>/reviews/", TeacherReviewListAPIView.as_view(), name="list"),
    path("bookings/<uuid:booking_id>/reviews/", ReviewCreateAPIView.as_view(), name="create"),
]
