from django import forms

from .models import IdentityVerification, ProfessionalCredential


class IdentityVerificationForm(forms.ModelForm):
    class Meta:
        model = IdentityVerification
        fields = ("document_type", "document")


class ProfessionalCredentialForm(forms.ModelForm):
    class Meta:
        model = ProfessionalCredential
        fields = ("credential_type", "title", "institution", "issued_year", "document")
