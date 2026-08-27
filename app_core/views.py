from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from profiles.models import TeacherProfile

from .forms import ContactForm


class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["featured_teachers"] = (
            TeacherProfile.objects.filter(is_public=True, user__is_active=True)
            .select_related("user")
            .prefetch_related("subjects", "teaching_modes")[:3]
        )
        return context


class AboutView(TemplateView):
    template_name = "about.html"


class PrivacyView(TemplateView):
    template_name = "privacy.html"


class TermsView(TemplateView):
    template_name = "terms.html"


class AcademicIntegrityView(TemplateView):
    template_name = "academic_integrity.html"


class ContactView(FormView):
    form_class = ContactForm
    template_name = "contact.html"
    success_url = reverse_lazy("contact")

    def get_initial(self):
        initial = super().get_initial()
        if self.request.user.is_authenticated:
            initial.update(
                name=self.request.user.get_full_name(),
                email=self.request.user.email,
            )
        return initial

    def form_valid(self, form):
        subject_label = dict(ContactForm.SUBJECT_CHOICES)[form.cleaned_data["subject"]]
        EmailMessage(
            subject=f"Contact MyKELASI - {subject_label}",
            body=(
                f"Nom : {form.cleaned_data['name']}\n"
                f"E-mail : {form.cleaned_data['email']}\n\n"
                f"{form.cleaned_data['message']}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.CONTACT_EMAIL],
            reply_to=[form.cleaned_data["email"]],
        ).send()
        messages.success(
            self.request,
            "Votre message a bien été envoyé. Notre équipe vous répondra rapidement.",
        )
        return super().form_valid(form)


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return Response({"status": "ok"})


@api_view(["GET"])
@permission_classes([AllowAny])
def ready(request):
    try:
        from django.db import connection

        connection.ensure_connection()
        return Response({"status": "ready", "database": "connected"})
    except Exception:
        return Response({"status": "error", "database": "unreachable"}, status=503)


@api_view(["GET"])
@permission_classes([AllowAny])
def api_schema(request):
    schema = {
        "openapi": "3.0.3",
        "info": {
            "title": "MyKELASI API",
            "description": "API REST MyKELASI pour Apprenants, Formateurs et Administration (Kinshasa, RDC)",
            "version": "1.0.0",
        },
        "paths": {
            "/api/v1/auth/register/": {"post": {"summary": "Inscription Apprenant ou Enseignant"}},
            "/api/v1/auth/login/": {"post": {"summary": "Obtention des jetons JWT"}},
            "/api/v1/auth/refresh/": {"post": {"summary": "Rafraîchissement du jeton JWT"}},
            "/api/v1/auth/logout/": {"post": {"summary": "Invalidation du jeton refresh"}},
            "/api/v1/auth/verify-email/": {"post": {"summary": "Vérification de l'adresse e-mail"}},
            "/api/v1/auth/me/": {"get": {"summary": "Profil utilisateur connecté"}},
            "/api/v1/search/teachers/": {"get": {"summary": "Recherche publique d'enseignants"}},
            "/api/v1/teacher/profile/": {
                "get": {"summary": "Consultation du profil enseignant privé"},
                "patch": {"summary": "Mise à jour du profil enseignant"},
            },
            "/api/v1/requests/": {
                "get": {"summary": "Liste des demandes de l'apprenant"},
                "post": {"summary": "Création d'une demande de cours"},
            },
            "/api/v1/bookings/": {
                "get": {"summary": "Liste des réservations"},
                "post": {"summary": "Création d'une réservation"},
            },
            "/api/v1/conversations/": {"get": {"summary": "Liste des conversations de l'utilisateur"}},
            "/api/v1/payments/webhook/": {"post": {"summary": "Webhook Mobile Money sandbox"}},
        },
    }
    return Response(schema)


@api_view(["GET"])
@permission_classes([AllowAny])
def api_root(request):
    return Response({"name": "MyKELASI API", "version": "v1"})
