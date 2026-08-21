from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse
from django.utils import timezone

from bookings.models import Booking
from bookings.services import create_booking, transition_booking
from learning.models import LearningRequest, Proposal
from notifications.models import Notification
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
    assert Notification.objects.filter(booking=booking).count() == 2
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
    assert not Notification.objects.exists()
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
    send_due_session_reminders(now=now)
    learner_notification = Notification.objects.get(booking=booking, user=learner)
    teacher_notification = Notification.objects.get(booking=booking, user=teacher)
    client.force_login(learner)

    response = client.get(reverse("notifications:list"))

    assert response.status_code == 200
    assert list(response.context["notifications"]) == [learner_notification]
    teacher_response = client.post(
        reverse("notifications:read", args=(teacher_notification.pk,))
    )
    learner_response = client.post(
        reverse("notifications:read", args=(learner_notification.pk,))
    )
    assert teacher_response.status_code == 404
    assert learner_response.status_code == 302
    learner_notification.refresh_from_db()
    assert learner_notification.read_at is not None
