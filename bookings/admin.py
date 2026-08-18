from django.contrib import admin

from .models import Booking, BookingTransition


class BookingTransitionInline(admin.TabularInline):
    model = BookingTransition
    extra = 0
    readonly_fields = ("from_status", "to_status", "actor", "reason", "created_at")
    can_delete = False


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("public_id", "learner", "teacher", "start_at", "status", "amount")
    list_filter = ("status", "teaching_mode")
    readonly_fields = ("public_id", "created_at", "updated_at")
    inlines = (BookingTransitionInline,)
