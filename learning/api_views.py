from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User

from .models import LearningEvent, LearningRequest, Proposal
from .serializers import LearningRequestSerializer, MatchResultSerializer, ProposalSerializer
from .services import generate_matches


class LearningRequestListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = LearningRequestSerializer

    def get_queryset(self):
        return LearningRequest.objects.filter(learner=self.request.user).select_related(
            "subject", "level", "teaching_mode", "service_area"
        )

    def perform_create(self, serializer):
        if self.request.user.account_type != User.AccountType.LEARNER:
            raise PermissionDenied("Réservé aux apprenants.")
        learning_request = serializer.save(learner=self.request.user)
        LearningEvent.objects.create(
            name=LearningEvent.Name.REQUEST_CREATED,
            actor=self.request.user,
            learning_request=learning_request,
        )
        generate_matches(learning_request)


class LearningRequestDetailAPIView(generics.RetrieveAPIView):
    serializer_class = LearningRequestSerializer
    lookup_field = "public_id"

    def get_queryset(self):
        return LearningRequest.objects.filter(learner=self.request.user)


class MatchListAPIView(APIView):
    def get(self, request, public_id):
        learning_request = get_object_or_404(
            LearningRequest,
            public_id=public_id,
            learner=request.user,
        )
        matches = generate_matches(learning_request)
        return Response(MatchResultSerializer(matches, many=True).data)


class ProposalListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ProposalSerializer

    def get_learning_request(self):
        return get_object_or_404(LearningRequest, public_id=self.kwargs["public_id"])

    def get_queryset(self):
        learning_request = self.get_learning_request()
        if self.request.user == learning_request.learner:
            return learning_request.proposals.select_related("teacher__user")
        if self.request.user.account_type == User.AccountType.TEACHER:
            if not learning_request.matches.filter(teacher__user=self.request.user).exists():
                raise PermissionDenied("Cette demande ne vous a pas été proposée.")
            return learning_request.proposals.filter(
                teacher__user=self.request.user
            ).select_related("teacher__user")
        raise PermissionDenied()

    def perform_create(self, serializer):
        learning_request = self.get_learning_request()
        if self.request.user.account_type != User.AccountType.TEACHER:
            raise PermissionDenied("Réservé aux enseignants.")
        if not learning_request.matches.filter(teacher__user=self.request.user).exists():
            raise PermissionDenied("Cette demande ne vous a pas été proposée.")
        teacher = self.request.user.teacher_profile
        if Proposal.objects.filter(learning_request=learning_request, teacher=teacher).exists():
            raise ValidationError("Vous avez déjà envoyé une proposition.")
        proposal = serializer.save(
            learning_request=learning_request,
            teacher=teacher,
        )
        LearningEvent.objects.create(
            name=LearningEvent.Name.PROPOSAL_SENT,
            actor=self.request.user,
            learning_request=learning_request,
            payload={"proposal_id": str(proposal.public_id)},
        )
