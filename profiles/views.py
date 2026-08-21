from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import DetailView, FormView, ListView

from accounts.models import User

from .filters import TeacherSearchFilter
from .forms import TeacherIdentityForm, TeacherOfferForm, TeacherPublishForm
from .models import TeacherProfile


class TeacherRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.account_type != User.AccountType.TEACHER:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_profile(self):
        profile, _ = TeacherProfile.objects.get_or_create(user=self.request.user)
        return profile


class TeacherIdentityView(TeacherRequiredMixin, FormView):
    template_name = "profiles/onboarding_identity.html"
    form_class = TeacherIdentityForm
    success_url = reverse_lazy("profiles:onboarding-offer")

    def get_initial(self):
        profile = self.get_profile()
        return {
            "first_name": self.request.user.first_name,
            "last_name": self.request.user.last_name,
            "headline": profile.headline,
            "bio": profile.bio,
            "years_experience": profile.years_experience,
            "languages": profile.languages,
        }

    @transaction.atomic
    def form_valid(self, form):
        user = self.request.user
        user.first_name = form.cleaned_data["first_name"]
        user.last_name = form.cleaned_data["last_name"]
        user.save(update_fields=("first_name", "last_name", "updated_at"))
        profile = self.get_profile()
        for field in ("headline", "bio", "years_experience", "languages"):
            setattr(profile, field, form.cleaned_data[field])
        profile.save()
        return super().form_valid(form)


class TeacherOfferView(TeacherRequiredMixin, FormView):
    template_name = "profiles/onboarding_offer.html"
    form_class = TeacherOfferForm
    success_url = reverse_lazy("profiles:onboarding-publish")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.get_profile()
        return kwargs

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class TeacherPublishView(TeacherRequiredMixin, FormView):
    template_name = "profiles/onboarding_publish.html"
    form_class = TeacherPublishForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["profile"] = self.get_profile()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile"] = self.get_profile()
        return context

    def form_valid(self, form):
        profile = self.get_profile()
        profile.is_public = True
        profile.save(update_fields=("is_public", "updated_at"))
        return redirect(profile)


class TeacherPublicDetailView(DetailView):
    model = TeacherProfile
    template_name = "profiles/teacher_detail.html"
    context_object_name = "teacher"
    slug_field = "public_id"
    slug_url_kwarg = "public_id"

    def get_queryset(self):
        return (
            TeacherProfile.objects.filter(is_public=True, user__is_active=True)
            .select_related("user")
            .prefetch_related("subjects", "levels", "teaching_modes", "service_areas")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["reviews"] = self.object.user.received_reviews.filter(
            status="PUBLISHED"
        ).select_related("reviewer", "response")
        context["trust_score"] = self.object.trust_score_snapshots.first()
        return context


class TeacherSearchView(ListView):
    model = TeacherProfile
    template_name = "profiles/teacher_search.html"
    context_object_name = "teachers"
    paginate_by = 12

    def get_queryset(self):
        queryset = (
            TeacherProfile.objects.filter(is_public=True, user__is_active=True)
            .select_related("user")
            .prefetch_related("subjects", "levels", "teaching_modes", "service_areas")
        )
        self.filterset = TeacherSearchFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter"] = self.filterset
        query_params = self.request.GET.copy()
        query_params.pop("page", None)
        context["query_string"] = query_params.urlencode()
        return context
