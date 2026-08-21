from django.contrib import admin

from .models import Review, ReviewModerationAction, ReviewResponse, TrustScoreSnapshot


class ReviewModerationActionInline(admin.TabularInline):
    model = ReviewModerationAction
    extra = 0
    readonly_fields = ("actor", "action", "reason", "created_at")
    can_delete = False


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("public_id", "reviewer", "subject", "rating", "status", "created_at")
    list_filter = ("status", "rating")
    readonly_fields = ("public_id", "reviewer", "subject", "session", "created_at")
    inlines = (ReviewModerationActionInline,)


admin.site.register(ReviewResponse)


@admin.register(TrustScoreSnapshot)
class TrustScoreSnapshotAdmin(admin.ModelAdmin):
    list_display = ("teacher_profile", "score", "version", "source", "calculated_at")
    readonly_fields = (
        "teacher_profile",
        "score",
        "version",
        "components",
        "input_counts",
        "source",
        "calculated_at",
    )
