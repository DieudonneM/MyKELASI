from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.views.generic import CreateView, View

from .forms import IdentityVerificationForm, ProfessionalCredentialForm
from .models import IdentityVerification, ProfessionalCredential


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
        can_review = request.user.groups.filter(name="VERIFICATION").exists()
        if document.user_id != request.user.pk and not can_review and not request.user.is_superuser:
            raise PermissionDenied
        return FileResponse(document.document.open("rb"), as_attachment=True)
