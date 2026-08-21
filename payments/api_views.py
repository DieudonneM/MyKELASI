import json

from django.conf import settings
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

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
