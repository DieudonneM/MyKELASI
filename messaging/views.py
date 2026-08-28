from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import ListView

from learning.models import Proposal

from .forms import MessageForm, ReportForm
from .models import Message, Report, ReportAction
from .services import (
    conversations_for_user,
    create_conversation,
    create_report,
    create_target_report,
    get_reportable_target,
    mark_messages_read,
    record_moderator_view,
    send_message,
    transition_report,
)


class ConversationListView(LoginRequiredMixin, ListView):
    template_name = "messaging/conversation_list.html"
    context_object_name = "conversations"
    paginate_by = 12

    def get_queryset(self):
        return conversations_for_user(self.request.user).select_related(
            "learner", "teacher", "learning_request__subject"
        )


class ConversationStartView(LoginRequiredMixin, View):
    def post(self, request, proposal_id):
        proposal = get_object_or_404(Proposal, public_id=proposal_id)
        try:
            conversation = create_conversation(proposal=proposal, actor=request.user)
        except PermissionDenied:
            raise PermissionDenied from None
        return redirect(conversation)


class ConversationDetailView(LoginRequiredMixin, View):
    template_name = "messaging/conversation_detail.html"

    def get_conversation(self):
        return get_object_or_404(
            conversations_for_user(self.request.user).select_related(
                "learner", "teacher", "learning_request__subject"
            ),
            public_id=self.kwargs["public_id"],
        )

    def get(self, request, public_id):
        conversation = self.get_conversation()
        record_moderator_view(conversation=conversation, moderator=request.user)
        mark_messages_read(conversation=conversation, reader=request.user)
        page = Paginator(conversation.messages.select_related("author"), 30).get_page(
            request.GET.get("page")
        )
        return render(
            request,
            self.template_name,
            {"conversation": conversation, "message_page": page, "form": MessageForm()},
        )

    def post(self, request, public_id):
        conversation = self.get_conversation()
        form = MessageForm(request.POST)
        if form.is_valid():
            try:
                send_message(
                    conversation=conversation,
                    author=request.user,
                    content=form.cleaned_data["content"],
                )
            except (PermissionDenied, ValidationError) as error:
                form.add_error(None, error)
            else:
                return redirect(conversation)
        page = Paginator(conversation.messages.select_related("author"), 30).get_page(1)
        return render(
            request,
            self.template_name,
            {"conversation": conversation, "message_page": page, "form": form},
        )


class ReportCreateView(LoginRequiredMixin, View):
    template_name = "messaging/report_form.html"

    def get_context(self, request):
        conversation = get_object_or_404(
            conversations_for_user(request.user),
            public_id=self.kwargs["public_id"],
        )
        message = None
        if self.kwargs.get("message_id"):
            message = get_object_or_404(
                Message,
                public_id=self.kwargs["message_id"],
                conversation=conversation,
            )
        return conversation, message

    def get(self, request, public_id, message_id=None):
        conversation, message = self.get_context(request)
        return render(
            request,
            self.template_name,
            {"conversation": conversation, "message": message, "form": ReportForm()},
        )

    def post(self, request, public_id, message_id=None):
        conversation, message = self.get_context(request)
        form = ReportForm(request.POST)
        if form.is_valid():
            create_report(
                conversation=conversation,
                reporter=request.user,
                message=message,
                reason=form.cleaned_data["reason"],
                description=form.cleaned_data["description"],
            )
            messages.success(request, "Votre signalement a été transmis.")
            return redirect(conversation)
        return render(
            request,
            self.template_name,
            {"conversation": conversation, "message": message, "form": form},
        )


class TargetReportCreateView(LoginRequiredMixin, View):
    template_name = "messaging/report_form.html"

    def get_target(self, request):
        return get_reportable_target(
            target_type=self.kwargs["target_type"],
            public_id=self.kwargs["public_id"],
            user=request.user,
        )

    def get(self, request, target_type, public_id):
        target = self.get_target(request)
        return render(request, self.template_name, {"target": target, "form": ReportForm()})

    def post(self, request, target_type, public_id):
        target = self.get_target(request)
        form = ReportForm(request.POST)
        if form.is_valid():
            create_target_report(
                target_type=target_type,
                target=target,
                reporter=request.user,
                reason=form.cleaned_data["reason"],
                description=form.cleaned_data["description"],
            )
            messages.success(request, "Votre signalement a été transmis.")
            if target_type == "proposal":
                return redirect(target.learning_request)
            if target_type == "review":
                return redirect(target.session.booking.teacher.teacher_profile)
            return redirect(target)
        return render(request, self.template_name, {"target": target, "form": form})


class ModeratorRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if (
            request.user.is_authenticated
            and not request.user.groups.filter(name="MODERATION").exists()
        ):
            raise PermissionDenied("Accès réservé à la modération.")
        return super().dispatch(request, *args, **kwargs)


class ModerationReportListView(ModeratorRequiredMixin, ListView):
    template_name = "messaging/moderation_report_list.html"
    context_object_name = "reports"
    paginate_by = 20

    def get_queryset(self):
        return Report.objects.select_related(
            "reporter",
            "conversation__learner",
            "conversation__teacher",
            "teacher_profile__user",
            "proposal__teacher__user",
            "booking",
            "review__reviewer",
        )


class ModerationReportDetailView(ModeratorRequiredMixin, View):
    template_name = "messaging/moderation_report_detail.html"

    def get_report(self):
        return get_object_or_404(
            Report.objects.select_related(
                "reporter",
                "message__author",
                "conversation__learner",
                "conversation__teacher",
                "conversation__learning_request__subject",
                "teacher_profile__user",
                "proposal__teacher__user",
                "proposal__learning_request__subject",
                "booking__proposal__learning_request__subject",
                "review__reviewer",
                "review__subject",
            ),
            public_id=self.kwargs["public_id"],
        )

    def get(self, request, public_id):
        report = self.get_report()
        ReportAction.objects.create(
            report=report,
            actor=request.user,
            action=ReportAction.Action.VIEWED,
        )
        return render(request, self.template_name, {"report": report})

    def post(self, request, public_id):
        report = self.get_report()
        try:
            transition_report(
                report=report,
                moderator=request.user,
                action=request.POST.get("action", ""),
                note=request.POST.get("note", ""),
            )
        except ValidationError as error:
            messages.error(request, error.message)
        return redirect("messaging:moderation-detail", public_id=report.public_id)
