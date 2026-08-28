from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Avg, Count
from django.utils import timezone

from bookings.models import Booking, Session
from learning.models import LearningEvent
from verification.models import VerificationStatus

from .models import Review, ReviewModerationAction, ReviewResponse, TrustScoreSnapshot

TRUST_SCORE_VERSION = "trust-v1"


@transaction.atomic
def create_review(*, session, reviewer, rating, punctuality, communication, quality, comment=""):
    session = (
        Session.objects.select_for_update()
        .select_related("booking__proposal__learning_request", "booking__teacher__teacher_profile")
        .get(pk=session.pk)
    )
    booking = session.booking
    if booking.status != Booking.Status.COMPLETED:
        raise ValidationError("Un avis exige une session terminée.")
    if reviewer.pk not in (booking.learner_id, booking.teacher_id):
        raise PermissionDenied("Avis réservé aux participants.")
    if Review.objects.filter(session=session, reviewer=reviewer).exists():
        raise ValidationError("Vous avez déjà publié un avis pour cette session.")
    subject = booking.teacher if reviewer.pk == booking.learner_id else booking.learner
    review = Review(
        session=session,
        reviewer=reviewer,
        subject=subject,
        rating=rating,
        punctuality=punctuality,
        communication=communication,
        quality=quality,
        comment=comment.strip(),
    )
    review.full_clean()
    review.save()
    LearningEvent.objects.create(
        name=LearningEvent.Name.REVIEW_CREATED,
        actor=reviewer,
        learning_request=booking.proposal.learning_request,
        payload={"review_id": str(review.public_id), "session_id": session.pk},
    )
    from notifications.models import Notification
    from notifications.services import notify_users

    notify_users(
        users=(subject,),
        kind=Notification.Kind.REVIEW_CREATED,
        title="Nouvel avis reçu",
        body="Un participant a publié un avis sur votre session.",
        booking=booking,
    )
    recalculate_teacher_trust_score(
        teacher_profile=booking.teacher.teacher_profile,
        source="review.created",
    )
    return review


@transaction.atomic
def create_review_response(*, review, author, content):
    review = Review.objects.select_for_update().get(pk=review.pk)
    if author.pk != review.subject_id:
        raise PermissionDenied("Seule la personne évaluée peut répondre.")
    if hasattr(review, "response"):
        raise ValidationError("Une réponse existe déjà pour cet avis.")
    content = content.strip()
    if not content:
        raise ValidationError("La réponse ne peut pas être vide.")
    return ReviewResponse.objects.create(review=review, author=author, content=content)


@transaction.atomic
def moderate_review(*, review, moderator, action, reason):
    if not moderator.groups.filter(name="MODERATION").exists():
        raise PermissionDenied("Action réservée à la modération.")
    reason = reason.strip()
    if not reason:
        raise ValidationError("Une raison de modération est obligatoire.")
    review = (
        Review.objects.select_for_update()
        .select_related("session__booking__teacher__teacher_profile")
        .get(pk=review.pk)
    )
    actions = {
        "hide": (Review.Status.HIDDEN, ReviewModerationAction.Action.HIDDEN),
        "restore": (Review.Status.PUBLISHED, ReviewModerationAction.Action.RESTORED),
    }
    try:
        status, audit_action = actions[action]
    except KeyError:
        raise ValidationError("Action de modération inconnue.") from None
    review.status = status
    review.moderation_reason = reason
    review.moderated_by = moderator
    review.moderated_at = timezone.now()
    review.save(update_fields=("status", "moderation_reason", "moderated_by", "moderated_at"))
    ReviewModerationAction.objects.create(
        review=review,
        actor=moderator,
        action=audit_action,
        reason=reason,
    )
    recalculate_teacher_trust_score(
        teacher_profile=review.session.booking.teacher.teacher_profile,
        source=f"review.{action}",
    )
    return review


def recalculate_teacher_trust_score(*, teacher_profile, source):
    user = teacher_profile.user
    identity_approved = user.identity_verifications.filter(
        status=VerificationStatus.APPROVED
    ).exists()
    credential_approved = user.professional_credentials.filter(
        status=VerificationStatus.APPROVED
    ).exists()
    verification_score = (
        (40 if user.email_verified else 0)
        + (40 if identity_approved else 0)
        + (20 if credential_approved else 0)
    )
    components = {"verification": verification_score}
    weights = {"verification": 20}

    terminal_bookings = Booking.objects.filter(
        teacher=user,
        status__in=(
            Booking.Status.COMPLETED,
            Booking.Status.CANCELLED,
            Booking.Status.NO_SHOW,
        ),
    )
    terminal_count = terminal_bookings.count()
    completed = terminal_bookings.filter(status=Booking.Status.COMPLETED)
    completed_count = completed.count()
    if terminal_count:
        components["delivery"] = round(completed_count / terminal_count * 100, 2)
        weights["delivery"] = 30

    sessions = Session.objects.filter(booking__teacher=user)
    session_count = sessions.count()
    if session_count:
        present_count = sessions.filter(teacher_present_at__isnull=False).count()
        components["attendance"] = round(present_count / session_count * 100, 2)
        weights["attendance"] = 20

    review_values = Review.objects.filter(
        subject=user,
        status=Review.Status.PUBLISHED,
    ).aggregate(
        rating=Avg("rating"),
        punctuality=Avg("punctuality"),
        communication=Avg("communication"),
        quality=Avg("quality"),
        count=Count("id"),
    )
    review_count = review_values["count"]
    if review_count:
        average = (
            sum(
                review_values[field]
                for field in ("rating", "punctuality", "communication", "quality")
            )
            / 4
        )
        components["reviews"] = round(average / 5 * 100, 2)
        weights["reviews"] = 25

    learner_counts = list(
        completed.values("learner_id").annotate(total=Count("id")).values_list("total", flat=True)
    )
    if learner_counts:
        repeat_learners = sum(1 for count in learner_counts if count > 1)
        components["repeat_booking"] = round(
            repeat_learners / len(learner_counts) * 100,
            2,
        )
        weights["repeat_booking"] = 5

    total_weight = sum(weights.values())
    weighted_score = sum(components[name] * weight for name, weight in weights.items())
    score = Decimal(str(weighted_score / total_weight)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
    return TrustScoreSnapshot.objects.create(
        teacher_profile=teacher_profile,
        version=TRUST_SCORE_VERSION,
        score=score,
        components=components,
        input_counts={
            "terminal_bookings": terminal_count,
            "completed_sessions": completed_count,
            "sessions": session_count,
            "published_reviews": review_count,
            "distinct_completed_learners": len(learner_counts),
        },
        source=source,
    )
