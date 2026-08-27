from django.urls import path

from .views import (
    FinanceExportView,
    FinancePaymentDetailView,
    FinancePaymentListView,
    PaymentCreateView,
    ReceiptDetailView,
    ReceiptListView,
)

app_name = "payments"

urlpatterns = [
    path("", ReceiptListView.as_view(), name="receipt-list"),
    path("initier/<uuid:booking_id>/", PaymentCreateView.as_view(), name="create"),
    path("recu/<uuid:public_id>/", ReceiptDetailView.as_view(), name="receipt"),
    path("finance/", FinancePaymentListView.as_view(), name="finance-list"),
    path("finance/export.csv", FinanceExportView.as_view(), name="finance-export"),
    path(
        "finance/<uuid:public_id>/",
        FinancePaymentDetailView.as_view(),
        name="finance-detail",
    ),
]
