from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from bookings.models import Booking
from learning.models import LearningRequest

from .mfa import confirm_device, generate_secret
from .models import MfaDevice, User
from .roles import INTERNAL_ROLE_NAMES, has_internal_role
from .serializers import (
    CurrentUserSerializer,
    EmailTokenObtainPairSerializer,
    EmailVerificationSerializer,
    MfaCodeSerializer,
    MfaDeviceSerializer,
    RegistrationSerializer,
)
from .services import record_audit


def has_support_access(user):
    return has_internal_role(user, "SUPPORT", "ADMIN", "SUPER_ADMIN")


class RegisterAPIView(generics.CreateAPIView):
    serializer_class = RegistrationSerializer
    permission_classes = (AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "auth"


class LoginAPIView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "auth"


class RefreshAPIView(TokenRefreshView):
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "auth"


class VerifyEmailAPIView(generics.GenericAPIView):
    serializer_class = EmailVerificationSerializer
    permission_classes = (AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "auth"

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Adresse email vérifiée."})


class LogoutAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"refresh": "Ce champ est obligatoire."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            return Response({"refresh": "Jeton invalide."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CurrentUserAPIView(generics.RetrieveAPIView):
    serializer_class = CurrentUserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user


class InternalMfaEnrollAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        if not request.user.is_internal:
            return Response({"detail": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)
        device, created = MfaDevice.objects.get_or_create(
            user=request.user,
            defaults={"secret": generate_secret()},
        )
        if device.confirmed_at is not None:
            return Response({"detail": "MFA déjà confirmé."}, status=status.HTTP_409_CONFLICT)
        return Response(
            MfaDeviceSerializer(device).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class InternalMfaConfirmAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        if not request.user.is_internal:
            return Response({"detail": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)
        serializer = MfaCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device = getattr(request.user, "mfa_device", None)
        if device is None or not confirm_device(
            user=request.user,
            code=serializer.validated_data["code"],
        ):
            return Response({"detail": "Code MFA invalide."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "MFA confirmé."})


class SupportDashboardAPIView(APIView):
    def get(self, request):
        if not has_support_access(request.user):
            return Response({"detail": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)
        record_audit(actor=request.user, action="support.dashboard_view", target=request.user)
        users = (
            User.objects.filter(is_internal=False)
            .exclude(groups__name__in=INTERNAL_ROLE_NAMES)
            .values("id", "email", "first_name", "last_name", "status")
        )
        requests = LearningRequest.objects.select_related("learner").values(
            "id", "learner_id", "learner__email", "status", "created_at"
        )
        bookings = Booking.objects.select_related("learner", "teacher").values(
            "public_id", "learner_id", "teacher_id", "status", "start_at", "end_at"
        )
        return Response(
            {"users": list(users), "requests": list(requests), "bookings": list(bookings)}
        )
