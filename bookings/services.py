from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from learning.models import LearningEvent, LearningRequest, Proposal

from .models import Booking, BookingTransition

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
    if proposal.status != Proposal.Status.SENT:
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
}


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
    if rule["role"] == "participant" and actor.pk not in (
        booking.learner_id,
        booking.teacher_id,
    ):
        raise PermissionDenied("Action réservée aux participants.")

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

    return booking
