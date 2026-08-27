from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import AuditLog, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("email",)
    list_display = (
        "email",
        "account_type",
        "status",
        "email_verified",
        "phone_verified",
        "is_staff",
        "is_active",
    )
    list_filter = (
        "account_type",
        "status",
        "email_verified",
        "phone_verified",
        "is_staff",
        "is_active",
    )
    search_fields = ("email", "first_name", "last_name", "phone_number")
    readonly_fields = ("last_login", "date_joined", "created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Identité", {"fields": ("first_name", "last_name", "phone_number")}),
        (
            "Compte",
            {"fields": ("account_type", "status", "email_verified", "phone_verified")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Dates", {"fields": ("last_login", "date_joined", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "account_type",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "action", "target_type", "target_id", "actor")
    list_filter = ("action", "target_type")
    search_fields = ("target_id", "actor__email")
    readonly_fields = ("actor", "action", "target_type", "target_id", "metadata", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
