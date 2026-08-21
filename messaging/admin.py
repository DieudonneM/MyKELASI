from django.contrib import admin

from .models import Conversation, Message, Report, ReportAction


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("public_id", "learner", "teacher", "last_message_at")
    search_fields = ("learner__email", "teacher__email")
    readonly_fields = ("public_id", "created_at", "updated_at", "last_message_at")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("public_id", "conversation", "author", "created_at", "read_at")
    readonly_fields = ("public_id", "created_at", "read_at")


class ReportActionInline(admin.TabularInline):
    model = ReportAction
    extra = 0
    readonly_fields = ("actor", "action", "note", "created_at")
    can_delete = False


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("public_id", "reporter", "reason", "status", "created_at")
    list_filter = ("status", "reason")
    readonly_fields = ("public_id", "created_at", "updated_at")
    inlines = (ReportActionInline,)
