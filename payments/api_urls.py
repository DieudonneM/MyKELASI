from django.urls import path

from .api_views import PaymentCreateAPIView, PaymentDetailAPIView, PaymentWebhookAPIView

app_name = "payments-api"

urlpatterns = [
    path(
        "bookings/<uuid:booking_id>/payments/",
        PaymentCreateAPIView.as_view(),
        name="create",
    ),
    path("payments/<uuid:public_id>/", PaymentDetailAPIView.as_view(), name="detail"),
    path("payments/webhook/", PaymentWebhookAPIView.as_view(), name="webhook"),
]
