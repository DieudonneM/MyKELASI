from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import CreateView, ListView, View

from accounts.roles import has_internal_role
from accounts.services import record_audit
from notifications.models import Notification

from .forms import IdentityVerificationForm, ProfessionalCredentialForm
from .models import (
    IdentityVerification,
    ProfessionalCredential,
    VerificationDecision,
    VerificationStatus,
)


class VerificationRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not has_internal_role(request.user, "VERIFICATION"):
            raise PermissionDenied("Accès réservé à la vérification.")
        return super().dispatch(request, *args, **kwargs)


class VerificationQueueView(VerificationRequiredMixin, ListView):
    template_name = "verification/queue.html"
    context_object_name = "documents"

    def get_queryset(self):
        return list(IdentityVerification.objects.filter(status=VerificationStatus.PENDING)) + list(
            ProfessionalCredential.objects.filter(status=VerificationStatus.PENDING)
        )


class VerificationReviewView(VerificationRequiredMixin, View):
    def post(self, request, kind, pk):
        model = {"identity": IdentityVerification, "credential": ProfessionalCredential}.get(kind)
        if model is None:
            raise PermissionDenied
        item = get_object_or_404(model, pk=pk)
        new_status = request.POST.get("status", "")
        valid_statuses = {
            VerificationStatus.APPROVED,
            VerificationStatus.REJECTED,
            VerificationStatus.EXPIRED,
        }
        reason = request.POST.get("reason", "").strip()
        if new_status not in valid_statuses or (
            new_status == VerificationStatus.REJECTED and not reason
        ):
            messages.error(request, "Statut invalide ou motif de rejet manquant.")
            return redirect("verification:queue")
        previous_status = item.status
        item.status = new_status
        item.rejection_reason = reason
        item.reviewed_by = request.user
        item.reviewed_at = timezone.now()
        item.save(update_fields=("status", "rejection_reason", "reviewed_by", "reviewed_at"))
        VerificationDecision.objects.create(
            document_type=kind,
            document_id=item.pk,
            reviewer=request.user,
            from_status=previous_status,
            to_status=new_status,
            reason=reason,
        )
        record_audit(actor=request.user, action="verification.review", target=item)
        Notification.objects.create(
            user=item.user,
            kind=Notification.Kind.VERIFICATION_UPDATED,
            title="Vérification mise à jour",
            body="Le statut de votre document de vérification a été mis à jour.",
        )
        messages.success(request, "Décision enregistrée.")
        return redirect("verification:queue")


class IdentityVerificationCreateView(LoginRequiredMixin, CreateView):
    model = IdentityVerification
    form_class = IdentityVerificationForm
    template_name = "verification/identity_form.html"

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return "/compte/tableau-de-bord/"


class ProfessionalCredentialCreateView(LoginRequiredMixin, CreateView):
    model = ProfessionalCredential
    form_class = ProfessionalCredentialForm
    template_name = "verification/credential_form.html"

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return "/compte/tableau-de-bord/"


class PrivateDocumentView(LoginRequiredMixin, View):
    model_map = {
        "identity": IdentityVerification,
        "credential": ProfessionalCredential,
    }

    def get(self, request, kind, pk):
        model = self.model_map.get(kind)
        if model is None:
            raise PermissionDenied
        document = get_object_or_404(model.objects.select_related("user"), pk=pk)
        if not request.user.is_active or request.user.status != "ACTIVE":
            raise PermissionDenied
        if document.status == VerificationStatus.EXPIRED:
            raise Http404
        can_review = has_internal_role(request.user, "VERIFICATION")
        if document.user_id != request.user.pk and not can_review and not request.user.is_superuser:
            raise PermissionDenied
        if document.user_id != request.user.pk:
            record_audit(actor=request.user, action="verification.document_view", target=document)
        response = FileResponse(document.document.open("rb"), as_attachment=True)
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        return response
