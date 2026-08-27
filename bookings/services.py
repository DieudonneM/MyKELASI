from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from learning.models import LearningEvent, LearningRequest, Proposal

from .models import Booking, BookingTransition, Session

ACTIVE_BOOKING_STATUSES = (Booking.Status.PENDING, Booking.Status.CONFIRMED)
CANCELLATION_POLICY = (
    "Annulation gratuite au moins 24 heures avant la session. "
    "Toute annulation plus tardive est examinée manuellement."
)


def _has_conflict(teacher_id, start_at, end_at, exclude_booking_id=None):
    queryset = Booking.objects.filter(
        teacher_id=teacher_id,
        status__in=ACTIVE_BOOKING_STATUSES,
        start_at__lt=end_at,
        end_at__gt=start_at,
    )
    if exclude_booking_id:
        queryset = queryset.exclude(pk=exclude_booking_id)
    return queryset.exists()


@transaction.atomic
def create_booking(*, proposal, learner, start_at, end_at):
    proposal = (
        Proposal.objects.select_for_update()
        .select_related(
            "learning_request__learner",
            "learning_request__teaching_mode",
            "learning_request__service_area",
            "teacher__user",
        )
        .get(pk=proposal.pk)
    )
    if proposal.learning_request.learner_id != learner.pk:
        raise PermissionDenied("Cette proposition ne vous appartient pas.")
    if proposal.status not in (Proposal.Status.SENT, Proposal.Status.ACCEPTED):
        raise ValidationError("Cette proposition n'est plus disponible.")
    if hasattr(proposal, "booking"):
        raise ValidationError("Cette proposition possède déjà une réservation.")
    if start_at >= end_at:
        raise ValidationError("L'heure de fin doit être après l'heure de début.")
    if start_at <= timezone.now():
        raise ValidationError("La réservation doit être planifiée dans le futur.")

    teacher = proposal.teacher.user
    get_user_model().objects.select_for_update().get(pk=teacher.pk)
    if _has_conflict(teacher.pk, start_at, end_at):
        raise ValidationError("L'enseignant possède déjà une réservation sur ce créneau.")

    booking = Booking.objects.create(
        proposal=proposal,
        learner=learner,
        teacher=teacher,
        start_at=start_at,
        end_at=end_at,
        teaching_mode=proposal.learning_request.teaching_mode,
        service_area=proposal.learning_request.service_area,
        amount=proposal.amount,
        cancellation_policy=CANCELLATION_POLICY,
    )
    proposal.status = Proposal.Status.ACCEPTED
    proposal.save(update_fields=("status", "updated_at"))
    BookingTransition.objects.create(
        booking=booking,
        from_status="",
        to_status=Booking.Status.PENDING,
        actor=learner,
        reason="Réservation créée depuis une proposition acceptée.",
    )
    LearningEvent.objects.create(
        name=LearningEvent.Name.BOOKING_CREATED,
        actor=learner,
        learning_request=proposal.learning_request,
        payload={"booking_id": str(booking.public_id)},
    )
    from notifications.models import Notification
    from notifications.services import notify_users

    notify_users(
        users=(learner, teacher),
        kind=Notification.Kind.BOOKING_CREATED,
        title="Réservation créée",
        body="Une nouvelle réservation a été créée.",
        booking=booking,
    )
    return booking


TRANSITIONS = {
    "confirm": {
        "from": (Booking.Status.PENDING,),
        "to": Booking.Status.CONFIRMED,
        "role": "teacher",
    },
    "reject": {
        "from": (Booking.Status.PENDING,),
        "to": Booking.Status.REJECTED,
        "role": "teacher",
    },
    "cancel": {
        "from": (Booking.Status.PENDING, Booking.Status.CONFIRMED),
        "to": Booking.Status.CANCELLED,
        "role": "participant",
    },
    "complete": {
        "from": (Booking.Status.CONFIRMED,),
        "to": Booking.Status.COMPLETED,
        "role": "teacher",
    },
    "learner_no_show": {
        "from": (Booking.Status.CONFIRMED,),
        "to": Booking.Status.NO_SHOW,
        "role": "teacher",
    },
    "teacher_no_show": {
        "from": (Booking.Status.CONFIRMED,),
        "to": Booking.Status.NO_SHOW,
        "role": "learner",
    },
    "dispute": {
        "from": (
            Booking.Status.CONFIRMED,
            Booking.Status.COMPLETED,
            Booking.Status.NO_SHOW,
        ),
        "to": Booking.Status.DISPUTED,
        "role": "participant",
    },
}


@transaction.atomic
def mark_session_presence(*, booking, actor):
    booking = Booking.objects.select_for_update().get(pk=booking.pk)
    if booking.status != Booking.Status.CONFIRMED:
        raise ValidationError("La présence exige une réservation confirmée.")
    if actor.pk not in (booking.learner_id, booking.teacher_id):
        raise PermissionDenied("Action réservée aux participants.")
    if timezone.now() < booking.start_at:
        raise ValidationError("La présence ne peut pas être marquée avant le début prévu.")

    session, _ = Session.objects.select_for_update().get_or_create(booking=booking)
    now = timezone.now()
    field = "learner_present_at" if actor.pk == booking.learner_id else "teacher_present_at"
    if getattr(session, field) is None:
        setattr(session, field, now)
        if session.actual_started_at is None:
            session.actual_started_at = now
        session.save(update_fields=(field, "actual_started_at", "updated_at"))
    return session


@transaction.atomic
def transition_booking(*, booking, actor, action, reason=""):
    try:
        rule = TRANSITIONS[action]
    except KeyError:
        raise ValidationError("Action de réservation inconnue.") from None

    booking = Booking.objects.select_for_update().select_related("proposal").get(pk=booking.pk)
    if booking.status not in rule["from"]:
        raise ValidationError("Cette transition n'est pas autorisée.")
    if rule["role"] == "teacher" and actor.pk != booking.teacher_id:
        raise PermissionDenied("Action réservée à l'enseignant.")
    if rule["role"] == "learner" and actor.pk != booking.learner_id:
        raise PermissionDenied("Action réservée à l'apprenant.")
    if rule["role"] == "participant" and actor.pk not in (
        booking.learner_id,
        booking.teacher_id,
    ):
        raise PermissionDenied("Action réservée aux participants.")
    if action in ("complete", "learner_no_show", "teacher_no_show"):
        if timezone.now() < booking.end_at:
            raise ValidationError("Cette action est disponible après la fin prévue.")
    if action == "complete":
        try:
            session = booking.session
        except Session.DoesNotExist:
            raise ValidationError("Les présences doivent être enregistrées.") from None
        if not session.learner_present_at or not session.teacher_present_at:
            raise ValidationError("Les deux participants doivent être marqués présents.")

    previous_status = booking.status
    booking.status = rule["to"]
    booking.save(update_fields=("status", "updated_at"))
    BookingTransition.objects.create(
        booking=booking,
        from_status=previous_status,
        to_status=booking.status,
        actor=actor,
        reason=reason,
    )

    if action == "confirm":
        learning_request = booking.proposal.learning_request
        learning_request.status = LearningRequest.Status.CLOSED
        learning_request.save(update_fields=("status", "updated_at"))
    elif action == "reject":
        booking.proposal.status = Proposal.Status.REJECTED
        booking.proposal.save(update_fields=("status", "updated_at"))
    elif action == "complete":
        session.actual_ended_at = timezone.now()
        session.outcome = reason
        session.save(update_fields=("actual_ended_at", "outcome", "updated_at"))
        LearningEvent.objects.create(
            name=LearningEvent.Name.SESSION_COMPLETED,
            actor=actor,
            learning_request=booking.proposal.learning_request,
            payload={"booking_id": str(booking.public_id), "session_id": session.pk},
        )
        from notifications.models import Notification
        from notifications.services import notify_users

        notify_users(
            users=(booking.learner, booking.teacher),
            kind=Notification.Kind.SESSION_COMPLETED,
            title="Session terminée",
            body="Votre session est terminée. Vous pouvez maintenant laisser un avis.",
            booking=booking,
        )
    elif action in ("learner_no_show", "teacher_no_show"):
        session, _ = Session.objects.get_or_create(booking=booking)
        session.actual_ended_at = timezone.now()
        session.outcome = reason
        session.save(update_fields=("actual_ended_at", "outcome", "updated_at"))

    return booking
