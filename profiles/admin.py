from django.contrib import admin

from .models import (
    Availability,
    ConfigurationVersion,
    LearnerProfile,
    Level,
    ServiceArea,
    Subject,
    TeacherProfile,
    TeachingMode,
)

PROFILE_MODELS = (
    Subject,
    Level,
    TeachingMode,
    ServiceArea,
    LearnerProfile,
    TeacherProfile,
    Availability,
)


@admin.register(ConfigurationVersion)
class ConfigurationVersionAdmin(admin.ModelAdmin):
    list_display = ("key", "version", "created_by", "created_at")
    list_filter = ("key",)
    readonly_fields = ("key", "version", "value", "created_by", "created_at")

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


for model in PROFILE_MODELS:
    admin.site.register(model)
