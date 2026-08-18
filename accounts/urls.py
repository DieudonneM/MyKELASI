from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from .views import (
    DashboardView,
    LoginView,
    RegisterView,
    VerificationInvalidView,
    VerificationSentView,
    VerifyEmailView,
)

app_name = "accounts"

urlpatterns = [
    path("inscription/", RegisterView.as_view(), name="register"),
    path("connexion/", LoginView.as_view(), name="login"),
    path("deconnexion/", auth_views.LogoutView.as_view(), name="logout"),
    path("tableau-de-bord/", DashboardView.as_view(), name="dashboard"),
    path("verification-envoyee/", VerificationSentView.as_view(), name="verification-sent"),
    path("verifier-email/<str:token>/", VerifyEmailView.as_view(), name="verify-email"),
    path("verification-invalide/", VerificationInvalidView.as_view(), name="verification-invalid"),
    path(
        "mot-de-passe/oublie/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset_form.html",
            email_template_name="accounts/password_reset_email.txt",
            subject_template_name="accounts/password_reset_subject.txt",
            success_url=reverse_lazy("accounts:password-reset-done"),
        ),
        name="password-reset",
    ),
    path(
        "mot-de-passe/email-envoye/",
        auth_views.PasswordResetDoneView.as_view(template_name="accounts/password_reset_done.html"),
        name="password-reset-done",
    ),
    path(
        "mot-de-passe/nouveau/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            success_url=reverse_lazy("accounts:password-reset-complete"),
        ),
        name="password-reset-confirm",
    ),
    path(
        "mot-de-passe/termine/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html"
        ),
        name="password-reset-complete",
    ),
]
