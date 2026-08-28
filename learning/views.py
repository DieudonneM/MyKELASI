from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import CreateView, DetailView, ListView, View

from accounts.models import User

from .forms import DetailedLearningRequestForm, ProposalForm, ShortLearningRequestForm
from .models import LearningEvent, LearningRequest, Proposal
from .services import accept_proposal, generate_matches, reject_proposal


class LearnerRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.account_type != User.AccountType.LEARNER:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class TeacherRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.account_type != User.AccountType.TEACHER:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class LearningRequestCreateMixin(LearnerRequiredMixin, CreateView):
    model = LearningRequest
    template_name = "learning/request_form.html"

    def form_valid(self, form):
        form.instance.learner = self.request.user
        response = super().form_valid(form)
        LearningEvent.objects.create(
            name=LearningEvent.Name.REQUEST_CREATED,
            actor=self.request.user,
            learning_request=self.object,
        )
        generate_matches(self.object)
        return response


class LearningRequestCreateView(LearningRequestCreateMixin):
    form_class = ShortLearningRequestForm
    form_title = "Décrire mon besoin"
    form_intro = (
        "Commencez avec les informations essentielles. Vous pourrez préciser votre demande ensuite."
    )
    is_short_form = True


class DetailedLearningRequestCreateView(LearningRequestCreateMixin):
    form_class = DetailedLearningRequestForm
    form_title = "Préciser ma demande"
    form_intro = (
        "Ajoutez un créneau, une zone et une fréquence pour recevoir des "
        "correspondances plus précises."
    )
    is_short_form = False


class LearningRequestListView(LearnerRequiredMixin, ListView):
    template_name = "learning/request_list.html"
    context_object_name = "requests"
    paginate_by = 12

    def get_queryset(self):
        return LearningRequest.objects.filter(learner=self.request.user).select_related(
            "subject", "level", "teaching_mode", "service_area"
        )


class LearningRequestDetailView(LoginRequiredMixin, DetailView):
    model = LearningRequest
    template_name = "learning/request_detail.html"
    context_object_name = "learning_request"
    slug_field = "public_id"
    slug_url_kwarg = "public_id"

    def get_queryset(self):
        queryset = LearningRequest.objects.select_related(
            "learner", "subject", "level", "teaching_mode", "service_area"
        ).prefetch_related("matches__teacher__user", "proposals__teacher__user")
        if self.request.user.account_type == User.AccountType.LEARNER:
            return queryset.filter(learner=self.request.user)
        if self.request.user.account_type == User.AccountType.TEACHER:
            return queryset.filter(matches__teacher__user=self.request.user).distinct()
        return queryset.none()


class ProposalCreateView(TeacherRequiredMixin, CreateView):
    model = Proposal
    form_class = ProposalForm
    template_name = "learning/proposal_form.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.account_type == User.AccountType.TEACHER:
            self.learning_request = get_object_or_404(
                LearningRequest.objects.filter(
                    matches__teacher__user=request.user,
                    status__in=(LearningRequest.Status.OPEN, LearningRequest.Status.MATCHED),
                ).distinct(),
                public_id=kwargs["public_id"],
            )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["learning_request"] = self.learning_request
        return context

    def form_valid(self, form):
        teacher = self.request.user.teacher_profile
        if Proposal.objects.filter(
            learning_request=self.learning_request,
            teacher=teacher,
        ).exists():
            form.add_error(None, "Vous avez déjà envoyé une proposition pour cette demande.")
            return self.form_invalid(form)
        form.instance.learning_request = self.learning_request
        form.instance.teacher = teacher
        form.save()
        LearningEvent.objects.create(
            name=LearningEvent.Name.PROPOSAL_SENT,
            actor=self.request.user,
            learning_request=self.learning_request,
            payload={"proposal_id": str(form.instance.public_id)},
        )
        from notifications.models import Notification
        from notifications.services import notify_users

        notify_users(
            users=(self.learning_request.learner,),
            kind=Notification.Kind.PROPOSAL_CREATED,
            title="Nouvelle proposition reçue",
            body="Un formateur a répondu à votre demande.",
            proposal=form.instance,
        )
        return redirect(self.learning_request)


class ProposalActionView(LearnerRequiredMixin, View):
    def post(self, request, public_id, action):
        proposal = get_object_or_404(Proposal, public_id=public_id)
        try:
            handler = accept_proposal if action == "accept" else reject_proposal
            handler(proposal_id=proposal.public_id, learner=request.user)
        except (PermissionError, ValueError) as error:
            from django.contrib import messages

            messages.error(request, str(error))
        return redirect(proposal.learning_request)
