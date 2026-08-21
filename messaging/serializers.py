from rest_framework import serializers

from learning.models import Proposal

from .models import Conversation, Message, Report


class MessageSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.get_full_name", read_only=True)
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ("public_id", "author_name", "is_mine", "content", "read_at", "created_at")
        read_only_fields = fields

    def get_is_mine(self, obj):
        return obj.author_id == self.context["request"].user.pk


class ConversationSerializer(serializers.ModelSerializer):
    subject = serializers.CharField(source="learning_request.subject.name", read_only=True)
    participant_name = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ("public_id", "subject", "participant_name", "last_message_at", "created_at")

    def get_participant_name(self, obj):
        user = self.context["request"].user
        participant = obj.teacher if user.pk == obj.learner_id else obj.learner
        return participant.get_full_name() or "Utilisateur MyKELASI"


class ConversationCreateSerializer(serializers.Serializer):
    proposal_id = serializers.SlugRelatedField(
        source="proposal",
        slug_field="public_id",
        queryset=Proposal.objects.all(),
    )


class MessageCreateSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=4000, trim_whitespace=True)


class ReportCreateSerializer(serializers.Serializer):
    message_id = serializers.SlugRelatedField(
        source="message",
        slug_field="public_id",
        queryset=Message.objects.all(),
        required=False,
        allow_null=True,
    )
    reason = serializers.ChoiceField(choices=Report.Reason.choices)
    description = serializers.CharField(max_length=2000, required=False, allow_blank=True)
