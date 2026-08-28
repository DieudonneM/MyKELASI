from django.urls import path

from .api_views import (
    PaymentCancelAPIView,
    PaymentCreateAPIView,
    PaymentDetailAPIView,
    PaymentListAPIView,
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
    path("payments/", PaymentListAPIView.as_view(), name="list"),
    path("payments/<uuid:public_id>/", PaymentDetailAPIView.as_view(), name="detail"),
    path("payments/<uuid:public_id>/cancel/", PaymentCancelAPIView.as_view(), name="cancel"),
    path("payments/webhook/", PaymentWebhookAPIView.as_view(), name="webhook"),
    path(
        "teacher/earnings/summary/",
        TeacherEarningsSummaryAPIView.as_view(),
        name="teacher-earnings-summary",
    ),
    path(
        "teacher/transactions/",
        TeacherTransactionListAPIView.as_view(),
        name="teacher-transactions",
    ),
    path("teacher/payouts/", TeacherPayoutListAPIView.as_view(), name="teacher-payouts"),
]
