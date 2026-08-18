from rest_framework import serializers

from .models import TeacherProfile


class TeacherSearchSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.get_full_name", read_only=True)
    subjects = serializers.StringRelatedField(many=True)
    levels = serializers.StringRelatedField(many=True)
    teaching_modes = serializers.StringRelatedField(many=True)
    service_areas = serializers.StringRelatedField(many=True)
    url = serializers.CharField(source="get_absolute_url", read_only=True)

    class Meta:
        model = TeacherProfile
        fields = (
            "public_id",
            "full_name",
            "headline",
            "bio",
            "years_experience",
            "hourly_rate",
            "currency",
            "subjects",
            "levels",
            "teaching_modes",
            "service_areas",
            "url",
        )
