from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from bookings.models import Booking
from bookings.services import create_booking, transition_booking
from learning.models import LearningRequest, Proposal
from notifications.models import Notification, NotificationPreference
from notifications.services import send_due_session_reminders
from profiles.models import Level, ServiceArea, Subject, TeachingMode


@pytest.fixture
def booking_data(db):
    user_model = get_user_model()
    learner = user_model.objects.create_user(
        email="reminder-learner@example.com",
        password="Strong-password-2026",
        account_type="LEARNER",
        email_verified=True,
    )
    teacher = user_model.objects.create_user(
        email="reminder-teacher@example.com",
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
        description="Cours avec rappel.",
    )
    proposal = Proposal.objects.create(
        learning_request=learning_request,
        teacher=teacher.teacher_profile,
        amount=20000,
        message="Disponible pour cette session.",
    )
    return learner, teacher, learning_request, proposal


@pytest.mark.django_db
def test_due_reminders_are_sent_once_per_participant(booking_data):
    learner, teacher, _, proposal = booking_data
    now = timezone.now()
    start_at = now + timedelta(hours=23, minutes=58)
    booking = create_booking(
        proposal=proposal,
        learner=learner,
        start_at=start_at,
        end_at=start_at + timedelta(hours=1),
    )
    transition_booking(booking=booking, actor=teacher, action="confirm")

    assert send_due_session_reminders(now=now) == 2
    assert send_due_session_reminders(now=now) == 0
    assert (
        Notification.objects.filter(
            booking=booking,
            kind__startswith="SESSION_REMINDER",
        ).count()
        == 2
    )
    assert len(mail.outbox) == 2


@pytest.mark.django_db
def test_pending_or_out_of_window_booking_is_not_reminded(booking_data):
    learner, _, _, proposal = booking_data
    now = timezone.now()
    start_at = now + timedelta(hours=25)
    booking = create_booking(
        proposal=proposal,
        learner=learner,
        start_at=start_at,
        end_at=start_at + timedelta(hours=1),
    )

    assert booking.status == Booking.Status.PENDING
    assert send_due_session_reminders(now=now) == 0
    assert not Notification.objects.filter(kind__startswith="SESSION_REMINDER").exists()
    assert not mail.outbox


@pytest.mark.django_db
def test_user_only_sees_and_reads_own_notifications(client, booking_data):
    learner, teacher, _, proposal = booking_data
    now = timezone.now()
    start_at = now + timedelta(hours=1, minutes=2)
    booking = create_booking(
        proposal=proposal,
        learner=learner,
        start_at=start_at,
        end_at=start_at + timedelta(hours=1),
    )
    transition_booking(booking=booking, actor=teacher, action="confirm")
    assert (
        Notification.objects.filter(
            booking=booking,
            kind=Notification.Kind.BOOKING_CREATED,
        ).count()
        == 2
    )
    send_due_session_reminders(now=now)
    learner_notification = Notification.objects.get(
        booking=booking,
        user=learner,
        kind=Notification.Kind.SESSION_REMINDER_24H,
    )
    teacher_notification = Notification.objects.get(
        booking=booking,
        user=teacher,
        kind=Notification.Kind.SESSION_REMINDER_24H,
    )
    client.force_login(learner)

    response = client.get(reverse("notifications:list"))

    assert response.status_code == 200
    assert list(response.context["notifications"]) == [
        learner_notification,
        Notification.objects.get(
            booking=booking,
            user=learner,
            kind=Notification.Kind.BOOKING_CREATED,
        ),
    ]
    teacher_response = client.post(reverse("notifications:read", args=(teacher_notification.pk,)))
    learner_response = client.post(reverse("notifications:read", args=(learner_notification.pk,)))
    assert teacher_response.status_code == 404
    assert learner_response.status_code == 302
    learner_notification.refresh_from_db()
    assert learner_notification.read_at is not None


@pytest.mark.django_db
def test_notifications_api_is_private_and_supports_read_actions(booking_data):
    learner, teacher, _, proposal = booking_data
    notification = Notification.objects.create(
        user=learner,
        proposal=proposal,
        kind=Notification.Kind.MATCH_CREATED,
        title="Nouveau match",
        body="Un formateur correspond à votre demande.",
    )
    other = Notification.objects.create(
        user=teacher,
        proposal=proposal,
        kind=Notification.Kind.MATCH_CREATED,
        title="Nouveau match",
        body="Notification privée.",
    )
    client = APIClient()
    client.force_authenticate(learner)

    response = client.get(reverse("notifications-api:list"))
    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["route"] == (
        f"/learner-requests/{proposal.learning_request.public_id}"
    )

    assert client.post(reverse("notifications-api:read", args=(other.pk,))).status_code == 404
    assert client.post(reverse("notifications-api:read-all")).status_code == 204
    notification.refresh_from_db()
    assert notification.read_at is not None


@pytest.mark.django_db
def test_notification_preferences_are_created_and_updated_for_current_user(booking_data):
    learner, _, _, _ = booking_data
    client = APIClient()
    client.force_authenticate(learner)

    response = client.get(reverse("notifications-api:preferences"))
    assert response.status_code == 200
    assert response.data["email"] is True
    response = client.patch(
        reverse("notifications-api:preferences"),
        {"email": False, "push": False, "booking_reminders": False},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["email"] is False
    assert NotificationPreference.objects.get(user=learner).push is False
