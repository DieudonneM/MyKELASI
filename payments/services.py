import uuid
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from hashlib import sha256

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from accounts.services import record_audit
from bookings.models import Booking
from learning.models import LearningEvent

from .models import FinanceAction, LedgerEntry, Payment, PaymentWebhook, Payout, Refund
from .providers import get_payment_provider


@transaction.atomic
def create_payment(*, booking, payer, idempotency_key):
    idempotency_key = idempotency_key.strip()
    if not idempotency_key:
        raise ValidationError("Une clé d'idempotence est obligatoire.")
    existing = Payment.objects.filter(
        payer=payer,
        idempotency_key=idempotency_key,
    ).first()
    if existing:
        return existing, False

    booking = Booking.objects.select_for_update().get(pk=booking.pk)
    if payer.pk != booking.learner_id:
        raise PermissionDenied("Seul l'apprenant peut initier le paiement.")
    if booking.status != Booking.Status.CONFIRMED:
        raise ValidationError("Le paiement exige une réservation confirmée.")
    active_statuses = (Payment.Status.PENDING, Payment.Status.SUCCESS)
    if booking.payments.filter(status__in=active_statuses).exists():
        raise ValidationError("Cette réservation possède déjà un paiement actif.")

    provider = get_payment_provider(settings.PAYMENT_PROVIDER)
    try:
        payment = Payment.objects.create(
            booking=booking,
            payer=payer,
            amount=booking.amount,
            currency=booking.currency,
            provider=provider.code,
            idempotency_key=idempotency_key,
            commission_rate=settings.PAYMENT_COMMISSION_RATE,
        )
    except IntegrityError:
        return Payment.objects.get(
            payer=payer,
            idempotency_key=idempotency_key,
        ), False
    initiation = provider.initiate(
        reference=payment.reference,
        amount=payment.amount,
        currency=payment.currency,
    )
    payment.provider_reference = initiation.provider_reference
    payment.save(update_fields=("provider_reference", "updated_at"))
    return payment, True


def _validated_webhook_payment(payload):
    required_fields = (
        "event_id",
        "reference",
        "provider_reference",
        "status",
        "amount",
        "currency",
    )
    if any(not payload.get(field) for field in required_fields):
        raise ValidationError("Payload de paiement incomplet.")
    try:
        amount = Decimal(str(payload["amount"]))
    except (InvalidOperation, TypeError):
        raise ValidationError("Montant de paiement invalide.") from None
    try:
        payment = Payment.objects.select_for_update().select_related(
            "booking__proposal__learning_request"
        ).get(reference=payload["reference"])
    except (Payment.DoesNotExist, ValueError):
        raise ValidationError("Référence de paiement inconnue.") from None
    if amount != payment.amount or payload["currency"] != payment.currency:
        raise ValidationError("Montant ou devise du paiement invalide.")
    if payload["provider_reference"] != payment.provider_reference:
        raise ValidationError("Référence fournisseur invalide.")
    return payment


def _post_success_ledger(payment):
    commission = _commission_amount(payment)
    teacher_amount = payment.amount - commission
    _post_entries(
        payment,
        (
            {
                "account": LedgerEntry.Account.CASH,
                "entry_type": LedgerEntry.EntryType.DEBIT,
                "amount": payment.amount,
                "memo": "Encaissement du paiement",
            },
            {
                "account": LedgerEntry.Account.TEACHER_PAYABLE,
                "entry_type": LedgerEntry.EntryType.CREDIT,
                "amount": teacher_amount,
                "memo": "Montant dû à l'enseignant",
            },
            {
                "account": LedgerEntry.Account.PLATFORM_REVENUE,
                "entry_type": LedgerEntry.EntryType.CREDIT,
                "amount": commission,
                "memo": "Commission de la plateforme",
            },
        ),
    )


def _require_finance(actor):
    if not actor.groups.filter(name="FINANCE").exists():
        raise PermissionDenied("Action réservée au personnel finance.")


def _commission_amount(payment):
    return (payment.amount * payment.commission_rate).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def _post_entries(payment, entries):
    transaction_reference = uuid.uuid4()
    LedgerEntry.objects.bulk_create(
        LedgerEntry(
            payment=payment,
            transaction_reference=transaction_reference,
            currency=payment.currency,
            **entry,
        )
        for entry in entries
    )


@transaction.atomic
def process_payment_webhook(*, payload, raw_payload):
    payload_hash = sha256(raw_payload).hexdigest()
    existing = PaymentWebhook.objects.select_related("payment").filter(
        event_id=payload.get("event_id", "")
    ).first()
    if existing:
        if existing.payload_hash != payload_hash:
            raise ValidationError("Identifiant webhook réutilisé avec un autre contenu.")
        return existing.payment, False

    payment = _validated_webhook_payment(payload)
    statuses = {
        "success": Payment.Status.SUCCESS,
        "failed": Payment.Status.FAILED,
        "disputed": Payment.Status.DISPUTED,
    }
    try:
        new_status = statuses[payload["status"]]
    except KeyError:
        raise ValidationError("État fournisseur inconnu.") from None
    if payment.status != Payment.Status.PENDING and payment.status != new_status:
        raise ValidationError("Transition de paiement interdite.")

    state_changed = payment.status != new_status
    if state_changed:
        payment.status = new_status
        payment.save(update_fields=("status", "updated_at"))
        if new_status == Payment.Status.SUCCESS:
            _post_success_ledger(payment)
            from notifications.models import Notification
            from notifications.services import notify_users

            notify_users(
                users=(payment.payer, payment.booking.teacher),
                kind=Notification.Kind.PAYMENT_COMPLETED,
                title="Paiement confirmé",
                body="Le paiement de votre réservation a été confirmé.",
                booking=payment.booking,
            )
            LearningEvent.objects.create(
                name=LearningEvent.Name.PAYMENT_COMPLETED,
                actor=payment.payer,
                learning_request=payment.booking.proposal.learning_request,
                payload={
                    "payment_id": str(payment.public_id),
                    "amount": str(payment.amount),
                    "currency": payment.currency,
                },
            )
    PaymentWebhook.objects.create(
        event_id=payload["event_id"],
        payment=payment,
        payload_hash=payload_hash,
    )
    return payment, state_changed


@transaction.atomic
def refund_payment(*, payment, actor, reason):
    _require_finance(actor)
    reason = reason.strip()
    if not reason:
        raise ValidationError("Le motif du remboursement est obligatoire.")
    payment = Payment.objects.select_for_update().get(pk=payment.pk)
    if payment.status != Payment.Status.SUCCESS:
        raise ValidationError("Seul un paiement réussi peut être remboursé.")
    if hasattr(payment, "payout"):
        raise ValidationError("Un paiement déjà versé ne peut pas être remboursé.")
    if hasattr(payment, "refund"):
        return payment.refund, False

    commission = _commission_amount(payment)
    teacher_amount = payment.amount - commission
    refund = Refund.objects.create(
        payment=payment,
        amount=payment.amount,
        currency=payment.currency,
        status=Refund.Status.SUCCESS,
        reason=reason,
        created_by=actor,
    )
    _post_entries(
        payment,
        (
            {
                "account": LedgerEntry.Account.TEACHER_PAYABLE,
                "entry_type": LedgerEntry.EntryType.DEBIT,
                "amount": teacher_amount,
                "memo": "Annulation du montant dû à l'enseignant",
            },
            {
                "account": LedgerEntry.Account.PLATFORM_REVENUE,
                "entry_type": LedgerEntry.EntryType.DEBIT,
                "amount": commission,
                "memo": "Annulation de la commission",
            },
            {
                "account": LedgerEntry.Account.CASH,
                "entry_type": LedgerEntry.EntryType.CREDIT,
                "amount": payment.amount,
                "memo": "Remboursement à l'apprenant",
            },
        ),
    )
    payment.status = Payment.Status.REFUNDED
    payment.save(update_fields=("status", "updated_at"))
    FinanceAction.objects.create(
        actor=actor,
        payment=payment,
        action=FinanceAction.Action.REFUND_COMPLETED,
        note=reason,
    )
    record_audit(actor=actor, action="finance.refund", target=payment)
    return refund, True


@transaction.atomic
def create_payout(*, payment, actor, note=""):
    _require_finance(actor)
    payment = Payment.objects.select_for_update().select_related("booking__teacher").get(
        pk=payment.pk
    )
    if payment.status != Payment.Status.SUCCESS:
        raise ValidationError("Le versement exige un paiement réussi.")
    if hasattr(payment, "refund"):
        raise ValidationError("Un paiement remboursé ne peut pas être versé.")
    if hasattr(payment, "payout"):
        return payment.payout, False

    amount = payment.amount - _commission_amount(payment)
    payout = Payout.objects.create(
        payment=payment,
        teacher=payment.booking.teacher,
        amount=amount,
        currency=payment.currency,
        status=Payout.Status.PAID,
        note=note.strip(),
        created_by=actor,
    )
    _post_entries(
        payment,
        (
            {
                "account": LedgerEntry.Account.TEACHER_PAYABLE,
                "entry_type": LedgerEntry.EntryType.DEBIT,
                "amount": amount,
                "memo": "Extinction du montant dû à l'enseignant",
            },
            {
                "account": LedgerEntry.Account.CASH,
                "entry_type": LedgerEntry.EntryType.CREDIT,
                "amount": amount,
                "memo": "Versement à l'enseignant",
            },
        ),
    )
    FinanceAction.objects.create(
        actor=actor,
        payment=payment,
        action=FinanceAction.Action.PAYOUT_COMPLETED,
        note=note.strip(),
    )
    record_audit(actor=actor, action="finance.payout", target=payment)
    return payout, True


@transaction.atomic
def reconcile_payment(*, payment, actor, matched, note=""):
    _require_finance(actor)
    payment = Payment.objects.select_for_update().get(pk=payment.pk)
    payment.reconciliation_status = (
        Payment.ReconciliationStatus.MATCHED
        if matched
        else Payment.ReconciliationStatus.MISMATCH
    )
    payment.reconciled_by = actor
    payment.reconciled_at = timezone.now()
    payment.save(
        update_fields=(
            "reconciliation_status",
            "reconciled_by",
            "reconciled_at",
            "updated_at",
        )
    )
    FinanceAction.objects.create(
        actor=actor,
        payment=payment,
        action=FinanceAction.Action.RECONCILED,
        note=note.strip(),
    )
    record_audit(actor=actor, action="finance.reconcile", target=payment)
    return payment
