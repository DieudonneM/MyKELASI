from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from bookings.models import Booking

from .models import Notification, NotificationPreference


def notify_users(*, users, kind, title, body, booking=None, proposal=None, learning_request=None):
    return Notification.objects.bulk_create(
        [
            Notification(
                user=user,
                kind=kind,
                title=title,
                body=body,
                booking=booking,
                proposal=proposal,
                learning_request=learning_request,
            )
            for user in users
        ]
    )


REMINDERS = (
    (
        Notification.Kind.SESSION_REMINDER_24H,
        timedelta(hours=1),
        timedelta(hours=24),
        "dans moins de 24 heures",
    ),
    (
        Notification.Kind.SESSION_REMINDER_1H,
        timedelta(0),
        timedelta(hours=1),
        "dans moins d'une heure",
    ),
)


def _notification_content(booking, label):
    subject = booking.proposal.learning_request.subject.name
    local_start = timezone.localtime(booking.start_at)
    title = f"Votre session de {subject} commence {label}"
    body = (
        f"Votre session de {subject} est prévue le "
        f"{local_start:%d/%m/%Y à %H:%M}. Consultez votre réservation pour les détails."
    )
    return title, body


@transaction.atomic
def _send_reminder(*, booking, user, kind, label):
    preferences, _ = NotificationPreference.objects.get_or_create(user=user)
    if not preferences.email or not preferences.booking_reminders:
        return False
    title, body = _notification_content(booking, label)
    notification, _ = Notification.objects.select_for_update().get_or_create(
        user=user,
        booking=booking,
        kind=kind,
        defaults={"title": title, "body": body},
    )
    if notification.emailed_at:
        return False

    send_mail(
        subject=title,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
    notification.emailed_at = timezone.now()
    notification.save(update_fields=("emailed_at",))
    return True


def send_due_session_reminders(*, now=None):
    now = now or timezone.now()
    sent_count = 0
    for kind, minimum_delay, maximum_delay, label in REMINDERS:
        bookings = Booking.objects.filter(
            status=Booking.Status.CONFIRMED,
            start_at__gt=now + minimum_delay,
            start_at__lte=now + maximum_delay,
        ).select_related("learner", "teacher", "proposal__learning_request__subject")
        for booking in bookings:
            for user in (booking.learner, booking.teacher):
                sent_count += _send_reminder(
                    booking=booking,
                    user=user,
                    kind=kind,
                    label=label,
                )
    return sent_count
