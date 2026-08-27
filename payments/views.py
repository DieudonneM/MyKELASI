import csv
import uuid

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import DetailView, ListView

from accounts.services import record_audit
from bookings.models import Booking

from .forms import FinanceActionForm, PaymentCreateForm
from .models import LedgerEntry, Payment, PaymentWebhook, Payout, Refund
from .services import create_payment, create_payout, reconcile_payment, refund_payment


class PaymentCreateView(LoginRequiredMixin, View):
    template_name = "payments/payment_form.html"

    def get_booking(self, request):
        return get_object_or_404(
            Booking.objects.filter(learner=request.user, status=Booking.Status.CONFIRMED),
            public_id=self.kwargs["booking_id"],
        )

    def get(self, request, booking_id):
        booking = self.get_booking(request)
        form = PaymentCreateForm(initial={"idempotency_key": uuid.uuid4()})
        return render(request, self.template_name, {"booking": booking, "form": form})

    def post(self, request, booking_id):
        booking = self.get_booking(request)
        form = PaymentCreateForm(request.POST)
        if form.is_valid():
            try:
                payment, _ = create_payment(
                    booking=booking,
                    payer=request.user,
                    idempotency_key=form.cleaned_data["idempotency_key"],
                )
            except (PermissionDenied, ValidationError) as error:
                form.add_error(None, error)
            else:
                messages.success(request, "Paiement sandbox initié.")
                return redirect(payment)
        return render(request, self.template_name, {"booking": booking, "form": form})


class ReceiptListView(LoginRequiredMixin, ListView):
    template_name = "payments/receipt_list.html"
    context_object_name = "payments"
    paginate_by = 20

    def get_queryset(self):
        return Payment.objects.filter(
            Q(payer=self.request.user) | Q(booking__teacher=self.request.user)
        ).select_related("booking__learner", "booking__teacher")


class ReceiptDetailView(LoginRequiredMixin, DetailView):
    model = Payment
    template_name = "payments/receipt_detail.html"
    context_object_name = "payment"
    slug_field = "public_id"
    slug_url_kwarg = "public_id"

    def get_queryset(self):
        return ReceiptListView.get_queryset(self)


class FinanceRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.groups.filter(
            name="FINANCE"
        ).exists():
            raise PermissionDenied("Accès réservé au personnel finance.")
        return super().dispatch(request, *args, **kwargs)


class FinancePaymentListView(FinanceRequiredMixin, ListView):
    model = Payment
    template_name = "payments/finance_list.html"
    context_object_name = "payments"
    paginate_by = 20

    def get_queryset(self):
        return Payment.objects.select_related("payer", "booking__teacher")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["webhooks"] = PaymentWebhook.objects.select_related("payment")
        context["refunds"] = Refund.objects.select_related("payment")
        context["payouts"] = Payout.objects.select_related("payment", "teacher")
        context["ledger_entries"] = LedgerEntry.objects.select_related("payment")
        return context


class FinanceExportView(FinanceRequiredMixin, View):
    def get(self, request):
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="finance-export.csv"'
        writer = csv.writer(response)
        writer.writerow(("reference", "status", "amount", "currency", "created_at"))
        for payment in Payment.objects.order_by("created_at"):
            writer.writerow(
                (
                    payment.reference,
                    payment.status,
                    payment.amount,
                    payment.currency,
                    payment.created_at.isoformat(),
                )
            )
        record_audit(actor=request.user, action="finance.export", target=request.user)
        return response


class FinancePaymentDetailView(FinanceRequiredMixin, View):
    template_name = "payments/finance_detail.html"

    def get_payment(self):
        return get_object_or_404(
            Payment.objects.select_related("payer", "booking__teacher"),
            public_id=self.kwargs["public_id"],
        )

    def get(self, request, public_id):
        return render(
            request,
            self.template_name,
            {"payment": self.get_payment(), "form": FinanceActionForm()},
        )

    def post(self, request, public_id):
        payment = self.get_payment()
        form = FinanceActionForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data["action"]
            note = form.cleaned_data["note"]
            try:
                if action == "refund":
                    refund_payment(payment=payment, actor=request.user, reason=note)
                elif action == "payout":
                    create_payout(payment=payment, actor=request.user, note=note)
                else:
                    reconcile_payment(
                        payment=payment,
                        actor=request.user,
                        matched=action == "reconcile_match",
                        note=note,
                    )
            except (PermissionDenied, ValidationError) as error:
                form.add_error(None, error)
            else:
                messages.success(request, "Action finance enregistrée.")
                return redirect("payments:finance-detail", public_id=payment.public_id)
        return render(request, self.template_name, {"payment": payment, "form": form})
