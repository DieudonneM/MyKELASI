import json

from django.conf import settings
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import BasePermission

from bookings.models import Booking

from .models import Payment
from .providers import verify_webhook_signature
from .serializers import PaymentSerializer
from .services import create_payment, process_payment_webhook


class PaymentCreateAPIView(APIView):
    def post(self, request, booking_id):
        booking = get_object_or_404(
            Booking.objects.filter(learner=request.user, status=Booking.Status.CONFIRMED),
            public_id=booking_id,
        )
        idempotency_key = request.headers.get("Idempotency-Key", "")
        try:
            payment, created = create_payment(
                booking=booking,
                payer=request.user,
                idempotency_key=idempotency_key,
            )
        except DjangoPermissionDenied as error:
            raise PermissionDenied(str(error)) from None
        except DjangoValidationError as error:
            raise ValidationError(error.messages) from None
        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(PaymentSerializer(payment).data, status=response_status)


class PaymentDetailAPIView(generics.RetrieveAPIView):
    serializer_class = PaymentSerializer
    lookup_field = "public_id"

    def get_queryset(self):
        return Payment.objects.filter(
            Q(payer=self.request.user) | Q(booking__teacher=self.request.user)
        ).select_related("booking")


class PaymentWebhookAPIView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def post(self, request):
        raw_payload = request.body
        signature = request.headers.get("X-Payment-Signature", "")
        if not verify_webhook_signature(
            raw_payload,
            signature,
            settings.PAYMENT_WEBHOOK_SECRET,
        ):
            return Response(
                {"detail": "Signature invalide."},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            payload = json.loads(raw_payload)
            payment, changed = process_payment_webhook(
                payload=payload,
                raw_payload=raw_payload,
            )
        except (json.JSONDecodeError, UnicodeDecodeError):
            return Response(
                {"detail": "Payload JSON invalide."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except DjangoValidationError as error:
            return Response(
                {"detail": error.messages},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"status": payment.status, "changed": changed})


class IsTeacher(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.account_type == "TEACHER")


class TeacherEarningsSummaryAPIView(APIView):
    permission_classes = (IsTeacher,)

    def get(self, request):
        payments = Payment.objects.filter(booking__teacher=request.user, status=Payment.Status.SUCCESS)
        payouts = payments.filter(payout__isnull=False)
        total = sum((payment.amount for payment in payments), 0)
        paid = payouts.aggregate(value=Sum("payout__amount"))["value"] or 0
        return Response({
            "total_earnings": f"{total:.2f}",
            "pending_balance": f"{total - paid:.2f}",
            "paid_balance": f"{paid:.2f}",
            "currency": "CDF",
            "last_payout_at": payouts.order_by("-payout__created_at").values_list("payout__created_at", flat=True).first(),
        })


class TeacherTransactionListAPIView(generics.ListAPIView):
    permission_classes = (IsTeacher,)
    serializer_class = PaymentSerializer

    def get_queryset(self):
        return Payment.objects.filter(booking__teacher=self.request.user).select_related("booking")


class TeacherPayoutListAPIView(generics.ListAPIView):
    permission_classes = (IsTeacher,)

    def get(self, request):
        payouts = request.user.payouts.select_related("payment")
        return Response({"results": [
            {
                "id": payout.pk,
                "amount": str(payout.amount),
                "status": payout.status.lower(),
                "reference": str(payout.reference),
                "paid_at": payout.created_at,
            }
            for payout in payouts
        ]})
