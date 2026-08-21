from django.contrib import admin

from .models import Booking, BookingTransition, Session


class BookingTransitionInline(admin.TabularInline):
    model = BookingTransition
    extra = 0
    readonly_fields = ("from_status", "to_status", "actor", "reason", "created_at")
    can_delete = False


class SessionInline(admin.StackedInline):
    model = Session
    extra = 0
    readonly_fields = (
        "learner_present_at",
        "teacher_present_at",
        "actual_started_at",
        "actual_ended_at",
        "created_at",
        "updated_at",
    )


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("public_id", "learner", "teacher", "start_at", "status", "amount")
    list_filter = ("status", "teaching_mode")
    readonly_fields = ("public_id", "created_at", "updated_at")
    inlines = (SessionInline, BookingTransitionInline)
