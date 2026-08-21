from django.contrib import admin

from .models import FinanceAction, LedgerEntry, Payment, PaymentWebhook, Payout, Refund


class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Payment)
class PaymentAdmin(ReadOnlyAdmin):
    list_display = ("reference", "amount", "currency", "status", "created_at")
    list_filter = ("status", "provider", "currency")


admin.site.register(LedgerEntry, ReadOnlyAdmin)
admin.site.register(PaymentWebhook, ReadOnlyAdmin)
admin.site.register(Refund, ReadOnlyAdmin)
admin.site.register(Payout, ReadOnlyAdmin)
admin.site.register(FinanceAction, ReadOnlyAdmin)
