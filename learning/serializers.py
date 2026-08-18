from rest_framework import serializers

from .models import LearningRequest, MatchResult, Proposal


class LearningRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningRequest
        fields = (
            "public_id",
            "subject",
            "level",
            "teaching_mode",
            "service_area",
            "budget_max",
            "preferred_date",
            "preferred_start_time",
            "frequency",
            "description",
            "status",
            "created_at",
        )
        read_only_fields = ("public_id", "status", "created_at")


class MatchResultSerializer(serializers.ModelSerializer):
    teacher_id = serializers.UUIDField(source="teacher.public_id", read_only=True)
    teacher_name = serializers.CharField(source="teacher.user.get_full_name", read_only=True)
    teacher_url = serializers.CharField(source="teacher.get_absolute_url", read_only=True)

    class Meta:
        model = MatchResult
        fields = ("teacher_id", "teacher_name", "teacher_url", "score", "reasons")


class ProposalSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source="teacher.user.get_full_name", read_only=True)

    class Meta:
        model = Proposal
        fields = ("public_id", "teacher_name", "amount", "message", "status", "created_at")
        read_only_fields = ("public_id", "teacher_name", "status", "created_at")
