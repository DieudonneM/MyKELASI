import json
from datetime import time, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.mfa import totp_code
from accounts.models import AuditLog, MfaDevice
from accounts.tokens import make_email_verification_token
from bookings.models import Booking
from bookings.services import create_booking, mark_session_presence, transition_booking
from learning.models import LearningRequest, Proposal
from learning.services import generate_matches
from messaging.models import Report, ReportAction
from messaging.services import create_conversation, create_report, send_message, transition_report
from payments.models import FinanceAction, Payment
from payments.services import create_payment, process_payment_webhook, reconcile_payment
from profiles.models import Availability, Level, ServiceArea, Subject, TeachingMode
from verification.models import IdentityVerification, VerificationStatus

PASSWORD = "Strong-password-2026"


def api_client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


def create_teacher(*, email, subject, level, mode, area, user=None):
    teacher = user or get_user_model().objects.create_user(
        email=email,
        password=PASSWORD,
        account_type="TEACHER",
        email_verified=True,
        first_name="Aline",
        last_name="Ilunga",
    )
    profile = teacher.teacher_profile
    profile.headline = "Professeure de mathematiques"
    profile.bio = "Cours personnalises pour progresser durablement."
    profile.years_experience = 5
    profile.hourly_rate = Decimal("20000")
    profile.languages = "Francais"
    profile.is_public = True
    profile.save()
    profile.subjects.add(subject)
    profile.levels.add(level)
    profile.teaching_modes.add(mode)
    profile.service_areas.add(area)
    Availability.objects.create(
        teacher=profile,
        weekday=Availability.Weekday.MONDAY,
        start_time=time(8),
        end_time=time(12),
    )
    return teacher


def complete_booking(*, learner, teacher, proposal, offset_days, idempotency_key, event_id):
    start_at = timezone.now() + timedelta(days=offset_days)
    booking = create_booking(
        proposal=proposal,
        learner=learner,
        start_at=start_at,
        end_at=start_at + timedelta(hours=1),
    )
    booking = transition_booking(booking=booking, actor=teacher, action="confirm")
    payment = pay_booking(
        booking=booking,
        learner=learner,
        idempotency_key=idempotency_key,
        event_id=event_id,
    )
    Booking.objects.filter(pk=booking.pk).update(
        start_at=timezone.now() - timedelta(hours=2),
        end_at=timezone.now() - timedelta(hours=1),
    )
    booking.refresh_from_db()
    mark_session_presence(booking=booking, actor=learner)
    mark_session_presence(booking=booking, actor=teacher)
    return transition_booking(booking=booking, actor=teacher, action="complete"), payment


def pay_booking(*, booking, learner, idempotency_key, event_id):
    payment, created = create_payment(
        booking=booking,
        payer=learner,
        idempotency_key=idempotency_key,
    )
    assert created is True
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
    assert payment.status == Payment.Status.SUCCESS
    return payment


@pytest.mark.django_db
def test_learner_journey_from_registration_to_repeat_booking_and_review():
    client = APIClient()
    registration = client.post(
        "/api/v1/auth/register/",
        {
            "email": "learner-journey@example.com",
            "first_name": "David",
            "last_name": "Kanku",
            "account_type": "LEARNER",
            "password": PASSWORD,
            "password_confirm": PASSWORD,
        },
        format="json",
    )
    assert registration.status_code == 201
    learner = get_user_model().objects.get(email="learner-journey@example.com")
    assert (
        client.post(
            "/api/v1/auth/verify-email/",
            {"token": make_email_verification_token(learner)},
            format="json",
        ).status_code
        == 200
    )

    subject = Subject.objects.first()
    level = Level.objects.first()
    mode = TeachingMode.objects.first()
    area = ServiceArea.objects.first()
    teacher = create_teacher(
        email="teacher-journey@example.com",
        subject=subject,
        level=level,
        mode=mode,
        area=area,
    )
    learner_client = api_client_for(learner)
    profile = learner_client.patch(
        "/api/v1/learner/profile/",
        {
            "first_name": "David",
            "last_name": "Kanku",
            "interest_ids": [subject.pk],
            "level_ids": [level.pk],
            "preferred_service_area_id": area.pk,
        },
        format="json",
    )
    assert profile.status_code == 200
    search = learner_client.get(f"/api/v1/search/teachers/?subject={subject.pk}")
    assert search.status_code == 200
    assert search.data["count"] == 1
    request = LearningRequest.objects.create(
        learner=learner,
        subject=subject,
        level=level,
        teaching_mode=mode,
        service_area=area,
        budget_max=25000,
        description="Preparation aux examens.",
    )
    generate_matches(request)
    proposal = Proposal.objects.create(
        learning_request=request,
        teacher=teacher.teacher_profile,
        amount=20000,
        message="Je peux vous accompagner.",
    )
    first_booking, _ = complete_booking(
        learner=learner,
        teacher=teacher,
        proposal=proposal,
        offset_days=2,
        idempotency_key="learner-journey-1",
        event_id="learner-journey-payment-1",
    )
    review = learner_client.post(
        f"/api/v1/bookings/{first_booking.public_id}/reviews/",
        {
            "rating": 5,
            "comment": "Session utile.",
            "punctuality": 5,
            "communication": 5,
            "quality": 5,
        },
        format="json",
    )
    assert review.status_code == 201

    repeat_request = LearningRequest.objects.create(
        learner=learner,
        subject=subject,
        level=level,
        teaching_mode=mode,
        service_area=area,
        budget_max=25000,
        description="Deuxieme seance.",
    )
    repeat_proposal = Proposal.objects.create(
        learning_request=repeat_request,
        teacher=teacher.teacher_profile,
        amount=20000,
        message="Continuons le travail.",
    )
    repeat_booking, _ = complete_booking(
        learner=learner,
        teacher=teacher,
        proposal=repeat_proposal,
        offset_days=4,
        idempotency_key="learner-journey-2",
        event_id="learner-journey-payment-2",
    )

    assert Booking.objects.filter(learner=learner, status=Booking.Status.COMPLETED).count() == 2


@pytest.mark.django_db
def test_teacher_journey_from_verification_to_proposal_session_revenue_and_review(
    settings, tmp_path
):
    settings.PRIVATE_MEDIA_ROOT = tmp_path / "private-media"
    subject = Subject.objects.first()
    level = Level.objects.first()
    mode = TeachingMode.objects.first()
    area = ServiceArea.objects.first()
    client = APIClient()
    registration = client.post(
        "/api/v1/auth/register/",
        {
            "email": "teacher-full-journey@example.com",
            "first_name": "Aline",
            "last_name": "Ilunga",
            "account_type": "TEACHER",
            "password": PASSWORD,
            "password_confirm": PASSWORD,
        },
        format="json",
    )
    assert registration.status_code == 201
    teacher = get_user_model().objects.get(email="teacher-full-journey@example.com")
    assert (
        client.post(
            "/api/v1/auth/verify-email/",
            {"token": make_email_verification_token(teacher)},
            format="json",
        ).status_code
        == 200
    )
    teacher = create_teacher(
        email="teacher-full-journey@example.com",
        subject=subject,
        level=level,
        mode=mode,
        area=area,
        user=teacher,
    )
    teacher.teacher_profile.is_public = False
    teacher.teacher_profile.save(update_fields=("is_public",))
    verification = IdentityVerification.objects.create(
        user=teacher,
        document_type="PASSPORT",
        document=SimpleUploadedFile(
            "passport.pdf", b"%PDF-1.4 journey", content_type="application/pdf"
        ),
    )
    reviewer = get_user_model().objects.create_user(email="reviewer-journey@example.com")
    reviewer.groups.add(Group.objects.get(name="VERIFICATION"))
    review_response = api_client_for(reviewer).post(
        f"/api/v1/verification/identity/{verification.pk}/review/",
        {"status": "APPROVED", "rejection_reason": "Document conforme."},
        format="json",
    )
    assert review_response.status_code == 200
    verification.refresh_from_db()
    assert verification.status == VerificationStatus.APPROVED
    publication = api_client_for(teacher).patch(
        "/api/v1/teacher/profile/", {"is_public": True}, format="json"
    )
    assert publication.status_code == 200
    assert publication.data["is_public"] is True

    learner = get_user_model().objects.create_user(
        email="learner-for-teacher@example.com", password=PASSWORD, account_type="LEARNER"
    )
    request = LearningRequest.objects.create(
        learner=learner,
        subject=subject,
        level=level,
        teaching_mode=mode,
        service_area=area,
        budget_max=25000,
        description="Besoin de soutien.",
    )
    generate_matches(request)
    proposal = Proposal.objects.create(
        learning_request=request,
        teacher=teacher.teacher_profile,
        amount=20000,
        message="Disponible cette semaine.",
    )
    booking, _ = complete_booking(
        learner=learner,
        teacher=teacher,
        proposal=proposal,
        offset_days=2,
        idempotency_key="teacher-journey-1",
        event_id="teacher-journey-payment-1",
    )
    assert (
        api_client_for(learner)
        .post(
            f"/api/v1/bookings/{booking.public_id}/reviews/",
            {
                "rating": 5,
                "comment": "Tres bonne explication.",
                "punctuality": 5,
                "communication": 5,
                "quality": 5,
            },
            format="json",
        )
        .status_code
        == 201
    )

    earnings = api_client_for(teacher).get("/api/v1/teacher/earnings/summary/")
    received_reviews = api_client_for(teacher).get("/api/v1/teacher/reviews/")
    assert earnings.status_code == 200
    assert received_reviews.status_code == 200
    assert received_reviews.data["count"] == 1


@pytest.mark.django_db
def test_admin_journey_mfa_verification_moderation_finance_referential_analytics_and_audit(
    settings, tmp_path
):
    settings.PRIVATE_MEDIA_ROOT = tmp_path / "private-media"
    user_model = get_user_model()
    admin = user_model.objects.create_user(
        email="admin-journey@example.com",
        password=PASSWORD,
        is_internal=True,
        email_verified=True,
    )
    admin.groups.add(Group.objects.get(name="ADMIN"))
    admin.groups.add(Group.objects.get(name="FINANCE"))
    admin_client = api_client_for(admin)
    assert admin_client.post("/api/v1/auth/internal/mfa/enroll/").status_code == 201
    device = MfaDevice.objects.get(user=admin)
    assert (
        admin_client.post(
            "/api/v1/auth/internal/mfa/confirm/", {"code": totp_code(device.secret)}, format="json"
        ).status_code
        == 200
    )

    subject = Subject.objects.first()
    level = Level.objects.first()
    mode = TeachingMode.objects.first()
    area = ServiceArea.objects.first()
    teacher = create_teacher(
        email="admin-teacher@example.com", subject=subject, level=level, mode=mode, area=area
    )
    document = IdentityVerification.objects.create(
        user=teacher,
        document_type="PASSPORT",
        document=SimpleUploadedFile("admin.pdf", b"%PDF-1.4 admin", content_type="application/pdf"),
    )
    verifier = user_model.objects.create_user(email="admin-verifier@example.com", is_internal=True)
    verifier.groups.add(Group.objects.get(name="VERIFICATION"))
    verifier_client = api_client_for(verifier)
    assert verifier_client.get("/api/v1/verification/queue/").status_code == 200
    assert (
        verifier_client.post(
            f"/api/v1/verification/identity/{document.pk}/review/",
            {"status": "APPROVED", "rejection_reason": "Document conforme."},
            format="json",
        ).status_code
        == 200
    )

    learner = user_model.objects.create_user(
        email="admin-learner@example.com", account_type="LEARNER"
    )
    request = LearningRequest.objects.create(
        learner=learner,
        subject=subject,
        level=level,
        teaching_mode=mode,
        service_area=area,
        budget_max=25000,
        description="Parcours admin.",
    )
    proposal = Proposal.objects.create(
        learning_request=request,
        teacher=teacher.teacher_profile,
        amount=20000,
        message="Disponible.",
    )
    booking, payment = complete_booking(
        learner=learner,
        teacher=teacher,
        proposal=proposal,
        offset_days=2,
        idempotency_key="admin-journey-1",
        event_id="admin-journey-payment-1",
    )
    reconcile_payment(
        payment=payment,
        actor=admin,
        matched=True,
        note="Rapprochement de recette.",
    )
    conversation = create_conversation(proposal=proposal, actor=learner)
    message = send_message(conversation=conversation, author=teacher, content="Message a moderer.")
    report = create_report(
        conversation=conversation,
        reporter=learner,
        message=message,
        reason=Report.Reason.INAPPROPRIATE,
        description="A examiner.",
    )
    moderator = user_model.objects.create_user(
        email="admin-moderator@example.com", is_internal=True
    )
    moderator.groups.add(Group.objects.get(name="MODERATION"))
    transition_report(
        report=report, moderator=moderator, action="resolve", note="Cloture apres examen."
    )

    referential = admin_client.post(
        "/api/v1/internal/referentials/subjects/",
        {"name": "Robotique", "code": "robotique"},
        format="json",
    )
    assert referential.status_code == 201
    analytics = admin_client.get(f"/api/v1/analytics/?subject={subject.pk}&service_area={area.pk}")

    assert payment.status == Payment.Status.SUCCESS
    assert FinanceAction.objects.filter(
        actor=admin, payment=payment, action=FinanceAction.Action.RECONCILED
    ).exists()
    assert report.actions.filter(action=ReportAction.Action.RESOLVED).exists()
    assert analytics.status_code == 200
    assert analytics.data["completed_sessions"] == 1
    assert analytics.data["successful_payments"] == 1
    assert AuditLog.objects.filter(actor=admin, action="referential.create").exists()
    assert AuditLog.objects.filter(actor=admin, action="analytics.dashboard_view").exists()
