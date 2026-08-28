from rest_framework import serializers

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="pk", read_only=True)
    student_name = serializers.CharField(source="reviewer.get_full_name", read_only=True)
    reviewer_name = serializers.CharField(source="reviewer.get_full_name", read_only=True)
    response = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = (
            "id",
            "public_id",
            "student_name",
            "reviewer_name",
            "rating",
            "punctuality",
            "communication",
            "quality",
            "comment",
            "response",
            "created_at",
        )
        read_only_fields = fields

    def get_response(self, obj):
        if hasattr(obj, "response") and not obj.response.is_hidden:
            return {
                "id": obj.response.pk,
                "message": obj.response.content,
                "content": obj.response.content,
                "created_at": obj.response.created_at,
            }
        return None


class ReviewCreateSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
    punctuality = serializers.IntegerField(min_value=1, max_value=5)
    communication = serializers.IntegerField(min_value=1, max_value=5)
    quality = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(max_length=2000, required=False, allow_blank=True)


class ReviewReplySerializer(serializers.Serializer):
    message = serializers.CharField(max_length=2000)
