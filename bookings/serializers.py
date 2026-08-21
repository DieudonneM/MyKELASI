from datetime import timedelta

from rest_framework import serializers

from learning.models import Proposal

from .models import Booking, BookingTransition, Session


class BookingCreateSerializer(serializers.Serializer):
    proposal_id = serializers.SlugRelatedField(
        source="proposal",
        slug_field="public_id",
        queryset=Proposal.objects.filter(status=Proposal.Status.SENT),
    )
    start_at = serializers.DateTimeField()
    duration_minutes = serializers.IntegerField(min_value=30, max_value=480)

    def validate(self, attrs):
        attrs["end_at"] = attrs["start_at"] + timedelta(minutes=attrs["duration_minutes"])
        return attrs


class BookingTransitionSerializer(serializers.ModelSerializer):
    actor = serializers.StringRelatedField()

    class Meta:
        model = BookingTransition
        fields = ("from_status", "to_status", "actor", "reason", "created_at")


class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = (
            "learner_present_at",
            "teacher_present_at",
            "actual_started_at",
            "actual_ended_at",
            "outcome",
        )


class BookingSerializer(serializers.ModelSerializer):
    subject = serializers.CharField(source="proposal.learning_request.subject.name", read_only=True)
    learner = serializers.StringRelatedField()
    teacher = serializers.StringRelatedField()
    teaching_mode = serializers.StringRelatedField()
    service_area = serializers.StringRelatedField()
    transitions = BookingTransitionSerializer(many=True, read_only=True)
    session = SessionSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = (
            "public_id",
            "subject",
            "learner",
            "teacher",
            "start_at",
            "end_at",
            "teaching_mode",
            "service_area",
            "amount",
            "currency",
            "cancellation_policy",
            "status",
            "session",
            "transitions",
        )


class BookingActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(
        choices=(
            "confirm",
            "reject",
            "cancel",
            "mark_present",
            "complete",
            "learner_no_show",
            "teacher_no_show",
            "dispute",
        )
    )
    reason = serializers.CharField(max_length=500, allow_blank=True, required=False)
