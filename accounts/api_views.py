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

from .models import User
from .roles import INTERNAL_ROLE_NAMES
from .serializers import (
    CurrentUserSerializer,
    EmailTokenObtainPairSerializer,
    EmailVerificationSerializer,
    RegistrationSerializer,
)


def has_support_access(user):
    return user.is_authenticated and (
        user.is_superuser
        or user.groups.filter(name__in=("SUPPORT", "ADMIN", "SUPER_ADMIN")).exists()
    )


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


class SupportDashboardAPIView(APIView):
    def get(self, request):
        if not has_support_access(request.user):
            return Response({"detail": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)
        users = User.objects.filter(is_internal=False).exclude(
            groups__name__in=INTERNAL_ROLE_NAMES
        ).values(
            "id", "email", "first_name", "last_name", "status"
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
