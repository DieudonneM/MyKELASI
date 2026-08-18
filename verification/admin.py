from django.contrib import admin

from .models import IdentityVerification, ProfessionalCredential


@admin.register(IdentityVerification)
class IdentityVerificationAdmin(admin.ModelAdmin):
    list_display = ("user", "document_type", "status", "created_at")
    list_filter = ("status", "document_type")
    readonly_fields = ("user", "document", "created_at")


@admin.register(ProfessionalCredential)
class ProfessionalCredentialAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "credential_type", "status", "created_at")
    list_filter = ("status", "credential_type")
    readonly_fields = ("user", "document", "created_at")
