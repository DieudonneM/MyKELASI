from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core import signing
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView, View

from .forms import EmailAuthenticationForm, RegistrationForm
from .models import User
from .services import send_verification_email
from .tokens import read_email_verification_token


class RegisterView(FormView):
    form_class = RegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("accounts:verification-sent")

    def form_valid(self, form):
        user = form.save()
        send_verification_email(user, self.request)
        return super().form_valid(form)


class LoginView(auth_views.LoginView):
    authentication_form = EmailAuthenticationForm
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/dashboard.html"


class VerificationSentView(TemplateView):
    template_name = "accounts/verification_sent.html"


class VerifyEmailView(View):
    def get(self, request, token):
        try:
            payload = read_email_verification_token(token)
            user = User.objects.get(pk=payload["user_id"], email=payload["email"])
        except (signing.BadSignature, signing.SignatureExpired, User.DoesNotExist, KeyError):
            return redirect("accounts:verification-invalid")

        if not user.email_verified:
            user.email_verified = True
            user.save(update_fields=("email_verified", "updated_at"))
        messages.success(request, "Votre adresse email est vérifiée. Vous pouvez vous connecter.")
        return redirect("accounts:login")


class VerificationInvalidView(TemplateView):
    template_name = "accounts/verification_invalid.html"
