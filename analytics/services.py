from decimal import Decimal

from django.db.models import Count, Sum

from bookings.models import Booking
from learning.models import LearningRequest, MatchResult, Proposal
from payments.models import Payment

from .models import Event


def record_event(*, name, actor=None, context=None):
    return Event.objects.create(
        name=name,
        actor_hash=Event.anonymized_actor(actor),
        context=context or {},
    )


def _period_queryset(queryset, start=None, end=None):
    if start:
        queryset = queryset.filter(created_at__gte=start)
    if end:
        queryset = queryset.filter(created_at__lt=end)
    return queryset


def product_kpis(*, start=None, end=None, subject_id=None, service_area_id=None):
    requests = _period_queryset(LearningRequest.objects.all(), start, end)
    if subject_id:
        requests = requests.filter(subject_id=subject_id)
    if service_area_id:
        requests = requests.filter(service_area_id=service_area_id)
    request_ids = requests.values("pk")
    matches = MatchResult.objects.filter(learning_request_id__in=request_ids)
    proposals = Proposal.objects.filter(learning_request_id__in=request_ids)
    bookings = Booking.objects.filter(proposal__learning_request_id__in=request_ids)
    payments = Payment.objects.filter(booking__proposal__learning_request_id__in=request_ids)
    completed = bookings.filter(status=Booking.Status.COMPLETED)
    successful_payments = payments.filter(status=Payment.Status.SUCCESS)
    request_count = requests.count()
    booking_count = bookings.count()
    completed_pairs = list(
        completed.values("learner_id", "teacher_id")
        .annotate(total=Count("id"))
        .values_list("total", flat=True)
    )
    match_count = matches.count()
    proposal_count = proposals.count()
    return {
        "requests": request_count,
        "matches": match_count,
        "proposals": proposal_count,
        "bookings": booking_count,
        "completed_sessions": completed.count(),
        "successful_payments": successful_payments.count(),
        "gmv": str(successful_payments.aggregate(value=Sum("amount"))["value"] or Decimal("0.00")),
        "commission": str(
            sum(
                (payment.amount * payment.commission_rate for payment in successful_payments),
                Decimal("0.00"),
            )
        ),
        "cancelled": bookings.filter(status=Booking.Status.CANCELLED).count(),
        "no_show": bookings.filter(status=Booking.Status.NO_SHOW).count(),
        "disputed": bookings.filter(status=Booking.Status.DISPUTED).count(),
        "request_to_booking_rate": round(booking_count / request_count * 100, 2)
        if request_count
        else 0,
        "booking_to_completed_rate": round(completed.count() / booking_count * 100, 2)
        if booking_count
        else 0,
        "response_rate": round(proposal_count / match_count * 100, 2) if match_count else 0,
        "repeat_booking_rate": round(
            sum(total > 1 for total in completed_pairs) / len(completed_pairs) * 100,
            2,
        )
        if completed_pairs
        else 0,
        "north_star_completed_sessions": completed.count(),
    }
