from django.urls import path

from .api_views import (
    CurrentUserAPIView,
    LoginAPIView,
    LogoutAPIView,
    RefreshAPIView,
    RegisterAPIView,
    VerifyEmailAPIView,
)

app_name = "accounts-api"

urlpatterns = [
    path("register/", RegisterAPIView.as_view(), name="register"),
    path("login/", LoginAPIView.as_view(), name="login"),
    path("refresh/", RefreshAPIView.as_view(), name="refresh"),
    path("logout/", LogoutAPIView.as_view(), name="logout"),
    path("verify-email/", VerifyEmailAPIView.as_view(), name="verify-email"),
    path("me/", CurrentUserAPIView.as_view(), name="me"),
]
