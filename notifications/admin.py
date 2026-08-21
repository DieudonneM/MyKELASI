from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "kind", "booking", "emailed_at", "read_at", "created_at")
    list_filter = ("kind", "emailed_at", "read_at")
    search_fields = ("user__email", "title")
    readonly_fields = ("created_at", "emailed_at")
