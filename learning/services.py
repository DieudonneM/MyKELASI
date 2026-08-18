from django.db import transaction

from profiles.models import TeacherProfile

from .models import LearningEvent, LearningRequest, MatchResult


def _score_teacher(learning_request, teacher):
    score = 0
    reasons = []

    if teacher.subjects.filter(pk=learning_request.subject_id).exists():
        score += 30
        reasons.append("Matière correspondante")
    if teacher.levels.filter(pk=learning_request.level_id).exists():
        score += 20
        reasons.append("Niveau correspondant")
    if teacher.teaching_modes.filter(pk=learning_request.teaching_mode_id).exists():
        score += 15
        reasons.append("Mode d'enseignement compatible")
    if not learning_request.service_area_id or teacher.service_areas.filter(
        pk=learning_request.service_area_id
    ).exists():
        score += 15
        reasons.append("Zone compatible")
    if teacher.hourly_rate is not None and teacher.hourly_rate <= learning_request.budget_max:
        score += 10
        reasons.append("Budget compatible")
    if learning_request.preferred_date and teacher.availabilities.filter(
        weekday=learning_request.preferred_date.isoweekday()
    ).exists():
        score += 10
        reasons.append("Disponible le jour souhaité")
    elif not learning_request.preferred_date and teacher.availabilities.exists():
        score += 10
        reasons.append("Disponibilités publiées")

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
    for score, teacher, reasons in ranked[:limit]:
        match, _ = MatchResult.objects.update_or_create(
            learning_request=learning_request,
            teacher=teacher,
            defaults={"score": score, "reasons": reasons},
        )
        selected_teacher_ids.append(teacher.pk)
        results.append(match)
    learning_request.matches.exclude(teacher_id__in=selected_teacher_ids).delete()
    learning_request.status = (
        LearningRequest.Status.MATCHED if results else LearningRequest.Status.OPEN
    )
    learning_request.save(update_fields=("status", "updated_at"))
    LearningEvent.objects.create(
        name=LearningEvent.Name.MATCH_CREATED,
        actor=learning_request.learner,
        learning_request=learning_request,
        payload={"match_count": len(results)},
    )
    return results
