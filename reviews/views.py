from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import ListView

from bookings.models import Booking, Session

from .forms import ReviewForm, ReviewResponseForm
from .models import Review
from .services import create_review, create_review_response, moderate_review


class ReviewCreateView(LoginRequiredMixin, View):
    template_name = "reviews/review_form.html"

    def get_booking(self, request):
        return get_object_or_404(
            Booking.objects.filter(Q(learner=request.user) | Q(teacher=request.user)),
            public_id=self.kwargs["booking_id"],
            status=Booking.Status.COMPLETED,
        )

    def get(self, request, booking_id):
        booking = self.get_booking(request)
        return render(request, self.template_name, {"booking": booking, "form": ReviewForm()})

    def post(self, request, booking_id):
        booking = self.get_booking(request)
        form = ReviewForm(request.POST)
        if form.is_valid():
            try:
                create_review(
                    session=get_object_or_404(Session, booking=booking),
                    reviewer=request.user,
                    **form.cleaned_data,
                )
            except (PermissionDenied, ValidationError) as error:
                form.add_error(None, error)
            else:
                messages.success(request, "Votre avis a été publié.")
                return redirect(booking)
        return render(request, self.template_name, {"booking": booking, "form": form})


class ReviewResponseCreateView(LoginRequiredMixin, View):
    template_name = "reviews/response_form.html"

    def get_review(self, request):
        return get_object_or_404(
            Review.objects.filter(subject=request.user, status=Review.Status.PUBLISHED),
            public_id=self.kwargs["public_id"],
        )

    def get(self, request, public_id):
        review = self.get_review(request)
        return render(
            request,
            self.template_name,
            {"review": review, "form": ReviewResponseForm()},
        )

    def post(self, request, public_id):
        review = self.get_review(request)
        form = ReviewResponseForm(request.POST)
        if form.is_valid():
            try:
                create_review_response(
                    review=review,
                    author=request.user,
                    content=form.cleaned_data["content"],
                )
            except (PermissionDenied, ValidationError) as error:
                form.add_error(None, error)
            else:
                return redirect(review.session.booking)
        return render(request, self.template_name, {"review": review, "form": form})


class ModeratorRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.groups.filter(
            name="MODERATION"
        ).exists():
            raise PermissionDenied("Accès réservé à la modération.")
        return super().dispatch(request, *args, **kwargs)


class ReviewModerationListView(ModeratorRequiredMixin, ListView):
    template_name = "reviews/moderation_list.html"
    context_object_name = "reviews"
    paginate_by = 20

    def get_queryset(self):
        return Review.objects.select_related("reviewer", "subject", "session__booking")


class ReviewModerationDetailView(ModeratorRequiredMixin, View):
    template_name = "reviews/moderation_detail.html"

    def get_review(self):
        return get_object_or_404(
            Review.objects.select_related("reviewer", "subject", "session__booking"),
            public_id=self.kwargs["public_id"],
        )

    def get(self, request, public_id):
        return render(request, self.template_name, {"review": self.get_review()})

    def post(self, request, public_id):
        review = self.get_review()
        try:
            moderate_review(
                review=review,
                moderator=request.user,
                action=request.POST.get("action", ""),
                reason=request.POST.get("reason", ""),
            )
        except ValidationError as error:
            messages.error(request, error.message)
        return redirect("reviews:moderation-detail", public_id=review.public_id)
