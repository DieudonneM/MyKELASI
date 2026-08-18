from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, FormView, ListView

from accounts.models import User
from learning.models import Proposal

from .forms import BookingActionForm, BookingCreateForm
from .models import Booking
from .services import create_booking, transition_booking


class BookingCreateView(LoginRequiredMixin, FormView):
    template_name = "bookings/booking_form.html"
    form_class = BookingCreateForm

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if request.user.is_authenticated and request.user.account_type != User.AccountType.LEARNER:
            raise PermissionDenied
        self.proposal = get_object_or_404(
            Proposal.objects.select_related("learning_request", "teacher__user"),
            public_id=kwargs["proposal_id"],
            learning_request__learner=request.user,
            status=Proposal.Status.SENT,
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["proposal"] = self.proposal
        return context

    def form_valid(self, form):
        try:
            booking = create_booking(
                proposal=self.proposal,
                learner=self.request.user,
                start_at=form.cleaned_data["start_at"],
                end_at=form.get_end_at(),
            )
        except ValidationError as error:
            form.add_error(None, error)
            return self.form_invalid(form)
        return redirect(booking)


class BookingListView(LoginRequiredMixin, ListView):
    template_name = "bookings/booking_list.html"
    context_object_name = "bookings"
    paginate_by = 12

    def get_queryset(self):
        queryset = Booking.objects.select_related(
            "learner",
            "teacher",
            "proposal__learning_request__subject",
            "teaching_mode",
            "service_area",
        )
        if self.request.user.account_type == User.AccountType.LEARNER:
            return queryset.filter(learner=self.request.user)
        if self.request.user.account_type == User.AccountType.TEACHER:
            return queryset.filter(teacher=self.request.user)
        return queryset.none()


class BookingDetailView(LoginRequiredMixin, DetailView):
    model = Booking
    template_name = "bookings/booking_detail.html"
    context_object_name = "booking"
    slug_field = "public_id"
    slug_url_kwarg = "public_id"

    def get_queryset(self):
        return Booking.objects.filter(
            Q(learner=self.request.user) | Q(teacher=self.request.user)
        ).select_related("learner", "teacher", "proposal__learning_request__subject")


class BookingActionView(LoginRequiredMixin, FormView):
    form_class = BookingActionForm
    template_name = "bookings/booking_action.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        self.booking = get_object_or_404(
            Booking.objects.filter(Q(learner=request.user) | Q(teacher=request.user)),
            public_id=kwargs["public_id"],
        )
        self.action = kwargs["action"]
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"booking": self.booking, "action": self.action})
        return context

    def form_valid(self, form):
        try:
            transition_booking(
                booking=self.booking,
                actor=self.request.user,
                action=self.action,
                reason=form.cleaned_data["reason"],
            )
        except (ValidationError, PermissionDenied) as error:
            form.add_error(None, error)
            return self.form_invalid(form)
        messages.success(self.request, "La réservation a été mise à jour.")
        return redirect(self.booking)
