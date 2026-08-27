from django.urls import path

from .api_views import (
    PaymentCreateAPIView,
    PaymentDetailAPIView,
    PaymentWebhookAPIView,
    TeacherEarningsSummaryAPIView,
    TeacherPayoutListAPIView,
    TeacherTransactionListAPIView,
)

app_name = "payments-api"

urlpatterns = [
    path(
        "bookings/<uuid:booking_id>/payments/",
        PaymentCreateAPIView.as_view(),
        name="create",
    ),
    path("payments/<uuid:public_id>/", PaymentDetailAPIView.as_view(), name="detail"),
    path("payments/webhook/", PaymentWebhookAPIView.as_view(), name="webhook"),
    path("teacher/earnings/summary/", TeacherEarningsSummaryAPIView.as_view(), name="teacher-earnings-summary"),
    path("teacher/transactions/", TeacherTransactionListAPIView.as_view(), name="teacher-transactions"),
    path("teacher/payouts/", TeacherPayoutListAPIView.as_view(), name="teacher-payouts"),
]
