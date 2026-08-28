from django.db import transaction
from django.db.models import Avg

from profiles.models import TeacherProfile
from profiles.services import matching_weights

from .models import LearningEvent, LearningRequest, MatchResult, Proposal


@transaction.atomic
def accept_proposal(*, proposal_id, learner):
    proposal = (
        Proposal.objects.select_for_update()
        .select_related("learning_request")
        .get(public_id=proposal_id)
    )
    request = LearningRequest.objects.select_for_update().get(pk=proposal.learning_request_id)
    if request.learner_id != learner.pk:
        raise PermissionError("Cette proposition ne vous appartient pas.")
    if proposal.status == Proposal.Status.ACCEPTED:
        return proposal
    if proposal.status != Proposal.Status.SENT or request.status == LearningRequest.Status.CLOSED:
        raise ValueError("Cette proposition n'est plus disponible.")
    Proposal.objects.filter(learning_request=request, status=Proposal.Status.SENT).exclude(
        pk=proposal.pk
    ).update(status=Proposal.Status.REJECTED)
    proposal.status = Proposal.Status.ACCEPTED
    proposal.save(update_fields=("status", "updated_at"))
    request.status = LearningRequest.Status.CLOSED
    request.save(update_fields=("status", "updated_at"))
    LearningEvent.objects.create(
        name=LearningEvent.Name.PROPOSAL_ACCEPTED,
        actor=learner,
        learning_request=request,
        payload={"proposal_id": str(proposal.public_id)},
    )
    _notify_proposal_participants(proposal, "accepted")
    return proposal


@transaction.atomic
def reject_proposal(*, proposal_id, learner):
    proposal = (
        Proposal.objects.select_for_update()
        .select_related("learning_request")
        .get(public_id=proposal_id)
    )
    if proposal.learning_request.learner_id != learner.pk:
        raise PermissionError("Cette proposition ne vous appartient pas.")
    if proposal.status == Proposal.Status.REJECTED:
        return proposal
    if proposal.status != Proposal.Status.SENT:
        raise ValueError("Cette proposition ne peut plus être refusée.")
    proposal.status = Proposal.Status.REJECTED
    proposal.save(update_fields=("status", "updated_at"))
    LearningEvent.objects.create(
        name=LearningEvent.Name.PROPOSAL_REJECTED,
        actor=learner,
        learning_request=proposal.learning_request,
        payload={"proposal_id": str(proposal.public_id)},
    )
    _notify_proposal_participants(proposal, "rejected")
    return proposal


def _notify_proposal_participants(proposal, status):
    from notifications.models import Notification

    kind = getattr(Notification.Kind, f"PROPOSAL_{status.upper()}")
    label = "acceptée" if status == "accepted" else "refusée"
    users = (proposal.learning_request.learner, proposal.teacher.user)
    for user in users:
        Notification.objects.create(
            user=user,
            proposal=proposal,
            kind=kind,
            title=f"Proposition {label}",
            body=f"La proposition de {proposal.teacher} a été {label}.",
        )


def _score_teacher(learning_request, teacher):
    default_weights = {
        "subject": 20,
        "level": 15,
        "teaching_mode": 10,
        "service_area": 10,
        "budget": 10,
        "availability": 10,
        "reliability": 10,
        "reputation": 10,
        "response_rate": 5,
    }
    weights = {**default_weights, **matching_weights()}
    score = 0
    reasons = []

    if teacher.subjects.filter(pk=learning_request.subject_id).exists():
        score += weights["subject"]
        reasons.append("Matière correspondante")
    if teacher.levels.filter(pk=learning_request.level_id).exists():
        score += weights["level"]
        reasons.append("Niveau correspondant")
    if teacher.teaching_modes.filter(pk=learning_request.teaching_mode_id).exists():
        score += weights["teaching_mode"]
        reasons.append("Mode d'enseignement compatible")
    if (
        not learning_request.service_area_id
        or teacher.service_areas.filter(pk=learning_request.service_area_id).exists()
    ):
        score += weights["service_area"]
        reasons.append("Zone compatible")
    if teacher.hourly_rate is not None and teacher.hourly_rate <= learning_request.budget_max:
        score += weights["budget"]
        reasons.append("Budget compatible")
    if (
        learning_request.preferred_date
        and teacher.availabilities.filter(
            weekday=learning_request.preferred_date.isoweekday()
        ).exists()
    ):
        score += weights["availability"]
        reasons.append("Disponible le jour souhaité")
    elif not learning_request.preferred_date and teacher.availabilities.exists():
        score += weights["availability"]
        reasons.append("Disponibilités publiées")

    from bookings.models import Booking
    from reviews.models import Review

    terminal_bookings = Booking.objects.filter(
        teacher=teacher.user,
        status__in=(
            Booking.Status.COMPLETED,
            Booking.Status.CANCELLED,
            Booking.Status.NO_SHOW,
        ),
    )
    terminal_count = terminal_bookings.count()
    if terminal_count:
        completed_count = terminal_bookings.filter(status=Booking.Status.COMPLETED).count()
        score += round(weights["reliability"] * completed_count / terminal_count)
        reasons.append("Fiabilité basée sur les sessions terminées")

    review_average = Review.objects.filter(
        subject=teacher.user,
        status=Review.Status.PUBLISHED,
    ).aggregate(average=Avg("rating"))["average"]
    if review_average is not None:
        score += round(weights["reputation"] * float(review_average) / 5)
        reasons.append("Réputation basée sur les avis publiés")

    match_queryset = MatchResult.objects.filter(teacher=teacher)
    match_count = match_queryset.count()
    if not match_queryset.filter(learning_request=learning_request).exists():
        match_count += 1
    proposal_count = teacher.proposals.count()
    if match_count:
        score += round(weights["response_rate"] * proposal_count / match_count)
        reasons.append("Taux de réponse basé sur les propositions envoyées")

    return score, reasons


@transaction.atomic
def generate_matches(learning_request, limit=5):
    candidates = (
        TeacherProfile.objects.filter(
            is_public=True,
            user__is_active=True,
            subjects=learning_request.subject,
        )
        .select_related("user")
        .prefetch_related("subjects", "levels", "teaching_modes", "service_areas")
        .distinct()
    )
    ranked = []
    for teacher in candidates:
        score, reasons = _score_teacher(learning_request, teacher)
        ranked.append((score, teacher, reasons))
    ranked.sort(key=lambda item: (-item[0], item[1].user.first_name, item[1].user.email))

    selected_teacher_ids = []
    results = []
    matches_changed = False
    for score, teacher, reasons in ranked[:limit]:
        match, created = MatchResult.objects.get_or_create(
            learning_request=learning_request,
            teacher=teacher,
            defaults={"score": score, "reasons": reasons},
        )
        match_changed = created or match.score != score or match.reasons != reasons
        if match_changed and not created:
            match.score = score
            match.reasons = reasons
            match.save(update_fields=("score", "reasons", "updated_at"))
        if match_changed:
            matches_changed = True
        selected_teacher_ids.append(teacher.pk)
        results.append(match)
    deleted_count, _ = learning_request.matches.exclude(
        teacher_id__in=selected_teacher_ids
    ).delete()
    matches_changed = matches_changed or deleted_count > 0
    learning_request.status = (
        LearningRequest.Status.MATCHED if results else LearningRequest.Status.OPEN
    )
    learning_request.save(update_fields=("status", "updated_at"))
    if matches_changed:
        LearningEvent.objects.create(
            name=LearningEvent.Name.MATCH_CREATED,
            actor=learning_request.learner,
            learning_request=learning_request,
            payload={"match_count": len(results)},
        )
        from notifications.models import Notification
        from notifications.services import notify_users

        notify_users(
            users=(learning_request.learner,),
            kind=Notification.Kind.MATCH_CREATED,
            title="Nouveaux formateurs trouvés",
            body=f"{len(results)} formateur(s) correspondent à votre demande.",
            learning_request=learning_request,
        )
    return results
