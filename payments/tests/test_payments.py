import json
from datetime import timedelta
from decimal import Decimal

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from bookings.services import create_booking, transition_booking
from learning.models import LearningRequest, Proposal
from payments.models import FinanceAction, LedgerEntry, Payment
from payments.providers import sign_webhook_payload
from payments.services import (
    create_payment,
    create_payout,
    process_payment_webhook,
    reconcile_payment,
    refund_payment,
)
from profiles.models import Level, ServiceArea, Subject, TeachingMode


@pytest.fixture
def confirmed_booking(db):
    user_model = get_user_model()
    learner = user_model.objects.create_user(
        email="payment-learner@example.com",
        password="test-password",
        account_type="LEARNER",
    )
    teacher = user_model.objects.create_user(
        email="payment-teacher@example.com",
        password="test-password",
        account_type="TEACHER",
    )
    learning_request = LearningRequest.objects.create(
        learner=learner,
        subject=Subject.objects.first(),
        level=Level.objects.first(),
        teaching_mode=TeachingMode.objects.first(),
        service_area=ServiceArea.objects.first(),
        budget_max=25000,
        description="Session à payer.",
    )
    proposal = Proposal.objects.create(
        learning_request=learning_request,
        teacher=teacher.teacher_profile,
        amount=20000,
        message="Disponible.",
    )
    start_at = timezone.now() + timedelta(days=2)
    booking = create_booking(
        proposal=proposal,
        learner=learner,
        start_at=start_at,
        end_at=start_at + timedelta(hours=1),
    )
    booking = transition_booking(booking=booking, actor=teacher, action="confirm")
    return learner, teacher, booking


@pytest.mark.django_db
def test_payment_creation_uses_booking_terms_and_is_idempotent(confirmed_booking):
    learner, _, booking = confirmed_booking
    payment, created = create_payment(
        booking=booking,
        payer=learner,
        idempotency_key="checkout-1",
    )
    repeated, repeated_created = create_payment(
        booking=booking,
        payer=learner,
        idempotency_key="checkout-1",
    )

    assert created is True
    assert repeated_created is False
    assert repeated == payment
    assert payment.amount == booking.amount
    assert payment.currency == booking.currency
    assert payment.provider_reference == f"sandbox-{payment.reference}"

    with pytest.raises(ValidationError, match="paiement actif"):
        create_payment(
            booking=booking,
            payer=learner,
            idempotency_key="checkout-2",
        )


def complete_payment(payment, event_id):
    payload = {
        "event_id": event_id,
        "reference": str(payment.reference),
        "provider_reference": payment.provider_reference,
        "status": "success",
        "amount": str(payment.amount),
        "currency": payment.currency,
    }
    raw_payload = json.dumps(payload, separators=(",", ":")).encode()
    process_payment_webhook(payload=payload, raw_payload=raw_payload)
    payment.refresh_from_db()


def finance_user():
    user = get_user_model().objects.create_user(
        email="finance@example.com",
        password="test-password",
        is_staff=True,
    )
    user.groups.add(Group.objects.get(name="FINANCE"))
    return user


@pytest.mark.django_db
def test_signed_webhook_is_strict_idempotent_and_balanced(confirmed_booking):
    learner, _, booking = confirmed_booking
    payment, _ = create_payment(
        booking=booking,
        payer=learner,
        idempotency_key="webhook-1",
    )
    client = APIClient()
    url = reverse("payments-api:webhook")
    payload = {
        "event_id": "sandbox-event-1",
        "reference": str(payment.reference),
        "provider_reference": payment.provider_reference,
        "status": "success",
        "amount": str(payment.amount),
        "currency": payment.currency,
    }
    raw_payload = json.dumps(payload, separators=(",", ":")).encode()

    invalid_signature = client.generic(
        "POST",
        url,
        raw_payload,
        content_type="application/json",
        HTTP_X_PAYMENT_SIGNATURE="invalid",
    )
    assert invalid_signature.status_code == 403

    tampered_payload = {**payload, "event_id": "sandbox-event-tampered", "amount": "1.00"}
    raw_tampered = json.dumps(tampered_payload, separators=(",", ":")).encode()
    tampered_response = client.generic(
        "POST",
        url,
        raw_tampered,
        content_type="application/json",
        HTTP_X_PAYMENT_SIGNATURE=sign_webhook_payload(
            raw_tampered,
            settings.PAYMENT_WEBHOOK_SECRET,
        ),
    )
    assert tampered_response.status_code == 400

    signature = sign_webhook_payload(raw_payload, settings.PAYMENT_WEBHOOK_SECRET)
    first_response = client.generic(
        "POST",
        url,
        raw_payload,
        content_type="application/json",
        HTTP_X_PAYMENT_SIGNATURE=signature,
    )
    repeated_response = client.generic(
        "POST",
        url,
        raw_payload,
        content_type="application/json",
        HTTP_X_PAYMENT_SIGNATURE=signature,
    )
    payment.refresh_from_db()

    assert first_response.status_code == 200
    assert first_response.data["changed"] is True
    assert repeated_response.status_code == 200
    assert repeated_response.data["changed"] is False
    assert payment.status == Payment.Status.SUCCESS
    assert payment.ledger_entries.count() == 3
    debits = sum(
        entry.amount
        for entry in payment.ledger_entries.filter(entry_type=LedgerEntry.EntryType.DEBIT)
    )
    credits = sum(
        entry.amount
        for entry in payment.ledger_entries.filter(entry_type=LedgerEntry.EntryType.CREDIT)
    )
    assert debits == credits == Decimal("20000.00")
    assert payment.booking.proposal.learning_request.events.filter(
        name="payment.completed"
    ).count() == 1

    entry = payment.ledger_entries.first()
    entry.memo = "Modification interdite"
    with pytest.raises(ValidationError, match="immuable"):
        entry.save()
    with pytest.raises(ValidationError, match="immuable"):
        entry.delete()


@pytest.mark.django_db
def test_full_refund_is_finance_only_audited_and_balanced(confirmed_booking):
    learner, teacher, booking = confirmed_booking
    payment, _ = create_payment(
        booking=booking,
        payer=learner,
        idempotency_key="refund-1",
    )
    complete_payment(payment, "refund-event-1")

    with pytest.raises(PermissionDenied):
        refund_payment(payment=payment, actor=teacher, reason="Interdit")
    refund, created = refund_payment(
        payment=payment,
        actor=finance_user(),
        reason="Session annulée après encaissement.",
    )
    payment.refresh_from_db()

    assert created is True
    assert refund.amount == payment.amount
    assert payment.status == Payment.Status.REFUNDED
    assert FinanceAction.objects.filter(
        payment=payment,
        action=FinanceAction.Action.REFUND_COMPLETED,
    ).exists()
    debits = sum(
        entry.amount
        for entry in payment.ledger_entries.filter(entry_type=LedgerEntry.EntryType.DEBIT)
    )
    credits = sum(
        entry.amount
        for entry in payment.ledger_entries.filter(entry_type=LedgerEntry.EntryType.CREDIT)
    )
    assert debits == credits == Decimal("40000.00")


@pytest.mark.django_db
def test_payout_and_reconciliation_are_audited(confirmed_booking):
    learner, _, booking = confirmed_booking
    payment, _ = create_payment(
        booking=booking,
        payer=learner,
        idempotency_key="payout-1",
    )
    complete_payment(payment, "payout-event-1")
    actor = finance_user()

    payout, created = create_payout(
        payment=payment,
        actor=actor,
        note="Versement sandbox confirmé.",
    )
    reconciled = reconcile_payment(
        payment=payment,
        actor=actor,
        matched=True,
        note="Référence fournisseur vérifiée.",
    )

    assert created is True
    assert payout.amount == Decimal("18000.00")
    assert reconciled.reconciliation_status == Payment.ReconciliationStatus.MATCHED
    assert FinanceAction.objects.filter(payment=payment).count() == 2
    debits = sum(
        entry.amount
        for entry in payment.ledger_entries.filter(entry_type=LedgerEntry.EntryType.DEBIT)
    )
    credits = sum(
        entry.amount
        for entry in payment.ledger_entries.filter(entry_type=LedgerEntry.EntryType.CREDIT)
    )
    assert debits == credits == Decimal("38000.00")


@pytest.mark.django_db
def test_payment_api_and_receipt_access_are_private(client, confirmed_booking):
    learner, teacher, booking = confirmed_booking
    outsider = get_user_model().objects.create_user(
        email="payment-outsider@example.com",
        password="test-password",
        account_type="LEARNER",
    )
    api_client = APIClient()
    api_client.force_authenticate(learner)
    create_url = reverse("payments-api:create", args=(booking.public_id,))

    created_response = api_client.post(
        create_url,
        {"amount": "1.00", "currency": "USD"},
        format="json",
        HTTP_IDEMPOTENCY_KEY="api-checkout-1",
    )
    repeated_response = api_client.post(
        create_url,
        {},
        format="json",
        HTTP_IDEMPOTENCY_KEY="api-checkout-1",
    )
    payment = Payment.objects.get(public_id=created_response.data["public_id"])

    assert created_response.status_code == 201
    assert repeated_response.status_code == 200
    assert payment.amount == booking.amount
    assert payment.currency == "CDF"

    detail_url = reverse("payments-api:detail", args=(payment.public_id,))
    api_client.force_authenticate(outsider)
    assert api_client.get(detail_url).status_code == 404
    api_client.force_authenticate(teacher)
    assert api_client.get(detail_url).status_code == 200

    receipt_url = reverse("payments:receipt", args=(payment.public_id,))
    client.force_login(outsider)
    assert client.get(receipt_url).status_code == 404
    client.force_login(learner)
    receipt_response = client.get(receipt_url)
    assert receipt_response.status_code == 200
    assert str(payment.reference) in receipt_response.content.decode()
