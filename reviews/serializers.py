from rest_framework import serializers

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.CharField(source="reviewer.get_full_name", read_only=True)
    response = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = (
            "public_id",
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
            return {"content": obj.response.content, "created_at": obj.response.created_at}
        return None


class ReviewCreateSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
    punctuality = serializers.IntegerField(min_value=1, max_value=5)
    communication = serializers.IntegerField(min_value=1, max_value=5)
    quality = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(max_length=2000, required=False, allow_blank=True)
