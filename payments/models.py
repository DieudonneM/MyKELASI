import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse

from bookings.models import Booking


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "En attente"
        SUCCESS = "SUCCESS", "Réussi"
        FAILED = "FAILED", "Échoué"
        REFUNDED = "REFUNDED", "Remboursé"
        DISPUTED = "DISPUTED", "Contesté"

    class ReconciliationStatus(models.TextChoices):
        UNRECONCILED = "UNRECONCILED", "Non rapproché"
        MATCHED = "MATCHED", "Rapproché"
        MISMATCH = "MISMATCH", "Écart constaté"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    booking = models.ForeignKey(Booking, on_delete=models.PROTECT, related_name="payments")
    payer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="payments",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3)
    provider = models.CharField(max_length=30)
    provider_reference = models.CharField(max_length=100, blank=True, unique=True, null=True)
    idempotency_key = models.CharField(max_length=100)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    commission_rate = models.DecimalField(max_digits=5, decimal_places=4)
    reconciliation_status = models.CharField(
        max_length=12,
        choices=ReconciliationStatus.choices,
        default=ReconciliationStatus.UNRECONCILED,
    )
    reconciled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reconciled_payments",
        null=True,
        blank=True,
    )
    reconciled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("payer", "idempotency_key"),
                name="unique_payment_idempotency_key_per_payer",
            ),
        ]

    def __str__(self):
        return f"{self.reference} - {self.amount} {self.currency}"

    def get_absolute_url(self):
        return reverse("payments:receipt", kwargs={"public_id": self.public_id})


class PaymentWebhook(models.Model):
    event_id = models.CharField(max_length=100, unique=True)
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="webhooks")
    payload_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)


class LedgerEntry(models.Model):
    class Account(models.TextChoices):
        CASH = "CASH", "Encaissement"
        TEACHER_PAYABLE = "TEACHER_PAYABLE", "Dû enseignant"
        PLATFORM_REVENUE = "PLATFORM_REVENUE", "Commission plateforme"

    class EntryType(models.TextChoices):
        DEBIT = "DEBIT", "Débit"
        CREDIT = "CREDIT", "Crédit"

    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="ledger_entries")
    transaction_reference = models.UUIDField(default=uuid.uuid4, editable=False)
    account = models.CharField(max_length=30, choices=Account.choices)
    entry_type = models.CharField(max_length=6, choices=EntryType.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3)
    memo = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="ledger_entry_positive_amount",
            ),
        ]

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("Une écriture comptable est immuable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Une écriture comptable est immuable.")


class Refund(models.Model):
    class Status(models.TextChoices):
        SUCCESS = "SUCCESS", "Réussi"
        FAILED = "FAILED", "Échoué"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    payment = models.OneToOneField(Payment, on_delete=models.PROTECT, related_name="refund")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3)
    status = models.CharField(max_length=10, choices=Status.choices)
    reason = models.TextField(max_length=2000)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_refunds",
    )
    created_at = models.DateTimeField(auto_now_add=True)


class Payout(models.Model):
    class Status(models.TextChoices):
        PAID = "PAID", "Versé"
        FAILED = "FAILED", "Échoué"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    payment = models.OneToOneField(Payment, on_delete=models.PROTECT, related_name="payout")
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="payouts",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3)
    status = models.CharField(max_length=10, choices=Status.choices)
    note = models.TextField(max_length=2000, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_payouts",
    )
    created_at = models.DateTimeField(auto_now_add=True)


class FinanceAction(models.Model):
    class Action(models.TextChoices):
        REFUND_COMPLETED = "REFUND_COMPLETED", "Remboursement effectué"
        PAYOUT_COMPLETED = "PAYOUT_COMPLETED", "Versement effectué"
        RECONCILED = "RECONCILED", "Paiement rapproché"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="finance_actions",
    )
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="finance_actions")
    action = models.CharField(max_length=20, choices=Action.choices)
    note = models.TextField(max_length=2000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)
