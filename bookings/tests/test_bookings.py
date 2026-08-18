from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from bookings.models import Booking, BookingTransition
from bookings.services import create_booking, transition_booking
from learning.models import LearningEvent, LearningRequest, Proposal
from profiles.models import Level, ServiceArea, Subject, TeachingMode


@pytest.fixture
def booking_data(db):
    user_model = get_user_model()
    learner = user_model.objects.create_user(
        email="learner@example.com",
        password="Strong-password-2026",
        account_type="LEARNER",
        email_verified=True,
    )
    teacher = user_model.objects.create_user(
        email="teacher@example.com",
        password="Strong-password-2026",
        account_type="TEACHER",
        email_verified=True,
    )
    learning_request = LearningRequest.objects.create(
        learner=learner,
        subject=Subject.objects.first(),
        level=Level.objects.first(),
        teaching_mode=TeachingMode.objects.first(),
        service_area=ServiceArea.objects.first(),
        budget_max=25000,
        description="Cours de préparation.",
    )
    proposal = Proposal.objects.create(
        learning_request=learning_request,
        teacher=teacher.teacher_profile,
        amount=20000,
        message="Disponible pour cette session.",
    )
    return learner, teacher, learning_request, proposal


def future_slot():
    start_at = timezone.now() + timedelta(days=2)
    return start_at, start_at + timedelta(hours=1)


@pytest.mark.django_db
def test_create_booking_copies_transaction_terms_and_audits(booking_data):
    learner, teacher, learning_request, proposal = booking_data
    start_at, end_at = future_slot()

    booking = create_booking(
        proposal=proposal,
        learner=learner,
        start_at=start_at,
        end_at=end_at,
    )

    assert booking.status == Booking.Status.PENDING
    assert booking.teacher == teacher
    assert booking.amount == proposal.amount
    assert booking.teaching_mode == learning_request.teaching_mode
    assert booking.transitions.get().to_status == Booking.Status.PENDING
    assert learning_request.events.filter(name=LearningEvent.Name.BOOKING_CREATED).exists()
    proposal.refresh_from_db()
    assert proposal.status == Proposal.Status.ACCEPTED


@pytest.mark.django_db
def test_overlapping_teacher_booking_is_rejected(booking_data):
    learner, teacher, _, proposal = booking_data
    start_at, end_at = future_slot()
    create_booking(proposal=proposal, learner=learner, start_at=start_at, end_at=end_at)
    second_request = LearningRequest.objects.create(
        learner=learner,
        subject=Subject.objects.first(),
        level=Level.objects.first(),
        teaching_mode=TeachingMode.objects.first(),
        service_area=ServiceArea.objects.first(),
        budget_max=25000,
        description="Autre cours.",
    )
    second_proposal = Proposal.objects.create(
        learning_request=second_request,
        teacher=teacher.teacher_profile,
        amount=18000,
        message="Autre proposition.",
    )

    with pytest.raises(ValidationError, match="déjà une réservation"):
        create_booking(
            proposal=second_proposal,
            learner=learner,
            start_at=start_at + timedelta(minutes=30),
            end_at=end_at + timedelta(minutes=30),
        )


@pytest.mark.django_db
def test_teacher_confirms_then_participant_cancels(booking_data):
    learner, teacher, learning_request, proposal = booking_data
    start_at, end_at = future_slot()
    booking = create_booking(
        proposal=proposal,
        learner=learner,
        start_at=start_at,
        end_at=end_at,
    )

    confirmed = transition_booking(
        booking=booking,
        actor=teacher,
        action="confirm",
        reason="Créneau disponible.",
    )
    assert confirmed.status == Booking.Status.CONFIRMED
    learning_request.refresh_from_db()
    assert learning_request.status == LearningRequest.Status.CLOSED

    cancelled = transition_booking(
        booking=confirmed,
        actor=learner,
        action="cancel",
        reason="Empêchement.",
    )
    assert cancelled.status == Booking.Status.CANCELLED
    assert BookingTransition.objects.filter(booking=booking).count() == 3


@pytest.mark.django_db
def test_learner_cannot_confirm_booking(booking_data):
    learner, _, _, proposal = booking_data
    start_at, end_at = future_slot()
    booking = create_booking(
        proposal=proposal,
        learner=learner,
        start_at=start_at,
        end_at=end_at,
    )

    with pytest.raises(PermissionDenied):
        transition_booking(booking=booking, actor=learner, action="confirm")


@pytest.mark.django_db
def test_outsider_cannot_read_booking(client, booking_data):
    learner, _, _, proposal = booking_data
    start_at, end_at = future_slot()
    booking = create_booking(
        proposal=proposal,
        learner=learner,
        start_at=start_at,
        end_at=end_at,
    )
    outsider = get_user_model().objects.create_user(
        email="outsider@example.com",
        password="Strong-password-2026",
        account_type="LEARNER",
    )
    client.force_login(outsider)

    assert client.get(booking.get_absolute_url()).status_code == 404


@pytest.mark.django_db
def test_anonymous_user_is_redirected_before_booking_lookup(client, booking_data):
    _, _, _, proposal = booking_data

    response = client.get(reverse("bookings:create", args=(proposal.public_id,)))

    assert response.status_code == 302
    assert reverse("accounts:login") in response.url


@pytest.mark.django_db
def test_api_creates_and_teacher_confirms_booking(booking_data):
    learner, teacher, _, proposal = booking_data
    start_at, _ = future_slot()
    client = APIClient()
    client.force_authenticate(learner)

    response = client.post(
        reverse("bookings-api:list"),
        {
            "proposal_id": str(proposal.public_id),
            "start_at": start_at.isoformat(),
            "duration_minutes": 60,
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.data["status"] == Booking.Status.PENDING

    client.force_authenticate(teacher)
    action_response = client.post(
        reverse("bookings-api:action", args=(response.data["public_id"],)),
        {"action": "confirm", "reason": "Confirmé."},
        format="json",
    )
    assert action_response.status_code == 200
    assert action_response.data["status"] == Booking.Status.CONFIRMED


@pytest.mark.django_db
def test_web_booking_flow_appears_in_both_dashboards(client, booking_data):
    learner, teacher, _, proposal = booking_data
    start_at, _ = future_slot()
    client.force_login(learner)

    response = client.post(
        reverse("bookings:create", args=(proposal.public_id,)),
        {
            "start_at": start_at.strftime("%Y-%m-%dT%H:%M"),
            "duration_minutes": 60,
        },
    )

    assert response.status_code == 302
    booking = Booking.objects.get(proposal=proposal)
    learner_dashboard = client.get(reverse("bookings:list"))
    assert learner_dashboard.status_code == 200
    assert booking in learner_dashboard.context["bookings"]

    client.force_login(teacher)
    teacher_dashboard = client.get(reverse("bookings:list"))
    assert teacher_dashboard.status_code == 200
    assert booking in teacher_dashboard.context["bookings"]
