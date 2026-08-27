from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core import signing
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import FormView, TemplateView, View

from .forms import EmailAuthenticationForm, RegistrationForm
from .models import User
from .services import record_audit, send_verification_email
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

    def form_valid(self, form):
        response = super().form_valid(form)
        record_audit(actor=self.request.user, action="auth.login", target=self.request.user)
        return response


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.account_type == User.AccountType.LEARNER:
            from bookings.models import Booking
            from learning.models import LearningRequest
            from messaging.models import Conversation
            from notifications.models import Notification

            context["recent_requests"] = LearningRequest.objects.filter(
                learner=user
            ).select_related("subject", "level")[:5]
            context["upcoming_bookings"] = Booking.objects.filter(
                learner=user,
                status__in=(Booking.Status.PENDING, Booking.Status.CONFIRMED),
                start_at__gte=timezone.now(),
            ).select_related("teacher", "proposal__learning_request__subject")[:5]
            context["unread_notifications"] = Notification.objects.filter(
                user=user, read_at__isnull=True
            ).count()
            context["active_conversations"] = Conversation.objects.filter(
                learner=user
            ).count()
        elif user.account_type == User.AccountType.TEACHER:
            from bookings.models import Booking
            from learning.models import Proposal
            from messaging.models import Conversation
            from notifications.models import Notification

            context["pending_proposals"] = Proposal.objects.filter(
                teacher__user=user, status=Proposal.Status.SENT
            ).count()
            context["upcoming_bookings"] = Booking.objects.filter(
                teacher=user,
                status__in=(Booking.Status.PENDING, Booking.Status.CONFIRMED),
                start_at__gte=timezone.now(),
            ).select_related("learner", "proposal__learning_request__subject")[:5]
            context["unread_notifications"] = Notification.objects.filter(
                user=user, read_at__isnull=True
            ).count()
            context["active_conversations"] = Conversation.objects.filter(
                teacher=user
            ).count()

        return context


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
            from notifications.models import Notification

            Notification.objects.create(
                user=user,
                kind=Notification.Kind.EMAIL_VERIFICATION,
                title="Adresse email vérifiée",
                body="Votre adresse email a été vérifiée avec succès.",
            )
        messages.success(request, "Votre adresse email est vérifiée. Vous pouvez vous connecter.")
        return redirect("accounts:login")


class VerificationInvalidView(TemplateView):
    template_name = "accounts/verification_invalid.html"


class AccountSettingsView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/settings.html"


class SupportDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/support_dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser and not request.user.groups.filter(
            name__in=("SUPPORT", "ADMIN", "SUPER_ADMIN")
        ).exists():
            from django.core.exceptions import PermissionDenied

            raise PermissionDenied("Accès réservé au support.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        from bookings.models import Booking
        from learning.models import LearningRequest

        context = super().get_context_data(**kwargs)
        from .roles import INTERNAL_ROLE_NAMES

        context["users"] = User.objects.filter(is_internal=False).exclude(
            groups__name__in=INTERNAL_ROLE_NAMES
        )
        context["requests"] = LearningRequest.objects.select_related("learner")
        context["bookings"] = Booking.objects.select_related("learner", "teacher")
        return context


class InternalDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/internal_dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser and not request.user.groups.filter(
            name__in=("SUPPORT", "VERIFICATION", "FINANCE", "MODERATION", "ADMIN", "SUPER_ADMIN")
        ).exists():
            from django.core.exceptions import PermissionDenied

            raise PermissionDenied("Accès réservé au personnel interne.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        from messaging.models import Report
        from payments.models import Payment
        from verification.models import IdentityVerification, ProfessionalCredential, VerificationStatus

        context = super().get_context_data(**kwargs)
        context["stats"] = {
            "total_users": User.objects.filter(is_internal=False).count(),
            "pending_verifications": (
                IdentityVerification.objects.filter(status=VerificationStatus.PENDING).count()
                + ProfessionalCredential.objects.filter(status=VerificationStatus.PENDING).count()
            ),
            "open_reports": Report.objects.filter(
                status__in=(Report.Status.OPEN, Report.Status.IN_REVIEW)
            ).count(),
            "pending_payments": Payment.objects.filter(
                status=Payment.Status.PENDING
            ).count(),
        }
        return context


class ReferentialsDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/referentials_dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser and not request.user.groups.filter(
            name__in=("ADMIN", "SUPER_ADMIN")
        ).exists():
            from django.core.exceptions import PermissionDenied

            raise PermissionDenied("Accès réservé aux administrateurs.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        from profiles.models import Level, ServiceArea, Subject, TeachingMode

        context = super().get_context_data(**kwargs)
        context["subjects_count"] = Subject.objects.filter(is_active=True).count()
        context["levels_count"] = Level.objects.filter(is_active=True).count()
        context["modes_count"] = TeachingMode.objects.filter(is_active=True).count()
        context["areas_count"] = ServiceArea.objects.filter(is_active=True).count()
        return context


class DeactivateAccountView(LoginRequiredMixin, View):
    def post(self, request):
        user = request.user
        user.status = User.Status.DEACTIVATED
        user.is_active = False
        user.save(update_fields=("status", "is_active", "updated_at"))
        logout(request)
        messages.info(request, "Votre compte a été désactivé.")
        return redirect("accounts:login")
