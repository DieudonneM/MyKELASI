from rest_framework import serializers

from .models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    route = serializers.SerializerMethodField()
    is_read = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ("id", "title", "body", "kind", "type", "route", "is_read", "created_at")
        read_only_fields = fields

    def get_type(self, obj):
        if obj.kind.startswith("PAYMENT"):
            return "payment"
        if obj.kind.startswith("REVIEW"):
            return "review"
        if obj.kind.startswith("SESSION") or obj.kind.startswith("BOOKING"):
            return "booking"
        if obj.kind.startswith("MATCH") or obj.kind.startswith("PROPOSAL"):
            return "booking"
        return "system"

    def get_route(self, obj):
        if obj.booking_id:
            return f"/learner-bookings/{obj.booking.public_id}"
        if obj.proposal_id:
            return f"/learner-requests/{obj.proposal.learning_request.public_id}"
        if obj.learning_request_id:
            return f"/learner-requests/{obj.learning_request.public_id}"
        if obj.kind == Notification.Kind.EMAIL_VERIFICATION:
            return "/email-verification"
        return "/notifications/"

    def get_is_read(self, obj):
        return obj.read_at is not None


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = ("email", "push", "sms", "booking_reminders")
