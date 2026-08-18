from django.urls import path

from .api_views import BookingActionAPIView, BookingDetailAPIView, BookingListCreateAPIView

app_name = "bookings-api"

urlpatterns = [
    path("bookings/", BookingListCreateAPIView.as_view(), name="list"),
    path("bookings/<uuid:public_id>/", BookingDetailAPIView.as_view(), name="detail"),
    path("bookings/<uuid:public_id>/action/", BookingActionAPIView.as_view(), name="action"),
]
