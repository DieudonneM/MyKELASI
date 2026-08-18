from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User

from .models import Booking
from .serializers import BookingActionSerializer, BookingCreateSerializer, BookingSerializer
from .services import create_booking, transition_booking


class BookingListCreateAPIView(generics.ListCreateAPIView):
    def get_serializer_class(self):
        return BookingCreateSerializer if self.request.method == "POST" else BookingSerializer

    def get_queryset(self):
        return Booking.objects.filter(
            Q(learner=self.request.user) | Q(teacher=self.request.user)
        ).select_related(
            "learner",
            "teacher",
            "proposal__learning_request__subject",
            "teaching_mode",
            "service_area",
        )

    def create(self, request, *args, **kwargs):
        if request.user.account_type != User.AccountType.LEARNER:
            raise PermissionDenied("Réservé aux apprenants.")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            booking = create_booking(
                proposal=serializer.validated_data["proposal"],
                learner=request.user,
                start_at=serializer.validated_data["start_at"],
                end_at=serializer.validated_data["end_at"],
            )
        except DjangoPermissionDenied as error:
            raise PermissionDenied(str(error)) from None
        except DjangoValidationError as error:
            raise ValidationError(error.messages) from None
        return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)


class BookingDetailAPIView(generics.RetrieveAPIView):
    serializer_class = BookingSerializer
    lookup_field = "public_id"

    def get_queryset(self):
        return Booking.objects.filter(
            Q(learner=self.request.user) | Q(teacher=self.request.user)
        ).select_related("learner", "teacher", "proposal__learning_request__subject")


class BookingActionAPIView(APIView):
    def post(self, request, public_id):
        booking = get_object_or_404(
            Booking.objects.filter(Q(learner=request.user) | Q(teacher=request.user)),
            public_id=public_id,
        )
        serializer = BookingActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            booking = transition_booking(
                booking=booking,
                actor=request.user,
                action=serializer.validated_data["action"],
                reason=serializer.validated_data.get("reason", ""),
            )
        except DjangoPermissionDenied as error:
            raise PermissionDenied(str(error)) from None
        except DjangoValidationError as error:
            raise ValidationError(error.messages) from None
        return Response(BookingSerializer(booking).data)
