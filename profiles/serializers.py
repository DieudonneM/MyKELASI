from rest_framework import serializers

from verification.models import IdentityVerification, VerificationStatus

from .models import (
    Availability,
    LearnerProfile,
    Level,
    ServiceArea,
    Subject,
    TeacherProfile,
    TeachingMode,
)


class TeacherProfileReferenceSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    code = serializers.SerializerMethodField()

    def get_code(self, obj):
        return getattr(obj, "code", None) or getattr(obj, "slug", "")


class TeacherProfileUserSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(read_only=True)
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    is_email_verified = serializers.BooleanField(source="email_verified", read_only=True)


class TeacherProfileSerializer(serializers.ModelSerializer):
    user = TeacherProfileUserSerializer(read_only=True)
    first_name = serializers.CharField(
        source="user.first_name", write_only=True, required=False, max_length=150
    )
    last_name = serializers.CharField(
        source="user.last_name", write_only=True, required=False, max_length=150
    )
    subjects = TeacherProfileReferenceSerializer(many=True, read_only=True)
    levels = TeacherProfileReferenceSerializer(many=True, read_only=True)
    teaching_modes = TeacherProfileReferenceSerializer(many=True, read_only=True)
    service_areas = TeacherProfileReferenceSerializer(many=True, read_only=True)
    subject_ids = serializers.PrimaryKeyRelatedField(
        source="subjects",
        queryset=Subject.objects.filter(is_active=True),
        many=True,
        write_only=True,
        required=False,
    )
    level_ids = serializers.PrimaryKeyRelatedField(
        source="levels",
        queryset=Level.objects.filter(is_active=True),
        many=True,
        write_only=True,
        required=False,
    )
    teaching_mode_ids = serializers.PrimaryKeyRelatedField(
        source="teaching_modes",
        queryset=TeachingMode.objects.filter(is_active=True),
        many=True,
        write_only=True,
        required=False,
    )
    service_area_ids = serializers.PrimaryKeyRelatedField(
        source="service_areas",
        queryset=ServiceArea.objects.filter(is_active=True),
        many=True,
        write_only=True,
        required=False,
    )
    completion_percentage = serializers.IntegerField(read_only=True)
    can_publish = serializers.BooleanField(read_only=True)
    missing_requirements = serializers.SerializerMethodField()

    class Meta:
        model = TeacherProfile
        fields = (
            "public_id",
            "user",
            "first_name",
            "last_name",
            "headline",
            "bio",
            "years_experience",
            "hourly_rate",
            "currency",
            "languages",
            "subjects",
            "levels",
            "teaching_modes",
            "service_areas",
            "subject_ids",
            "level_ids",
            "teaching_mode_ids",
            "service_area_ids",
            "completion_percentage",
            "missing_requirements",
            "is_public",
            "can_publish",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "public_id",
            "user",
            "currency",
            "subjects",
            "levels",
            "teaching_modes",
            "service_areas",
            "completion_percentage",
            "missing_requirements",
            "can_publish",
            "created_at",
            "updated_at",
        )

    def update(self, instance, validated_data):
        relation_data = {
            field: validated_data.pop(field)
            for field in ("subjects", "levels", "teaching_modes", "service_areas")
            if field in validated_data
        }
        user_data = validated_data.pop("user", {})
        user = instance.user
        for field, value in user_data.items():
            setattr(user, field, value)
        if user_data:
            user.save(update_fields=(*user_data.keys(), "updated_at"))
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        for field, value in relation_data.items():
            getattr(instance, field).set(value)
        return instance

    def validate_is_public(self, value):
        if value and not self.instance.can_publish:
            raise serializers.ValidationError(
                "Complétez le profil et vérifiez votre email avant publication."
            )
        return value

    def get_missing_requirements(self, profile):
        checks = (
            ("first_name", "Ajoutez votre prénom", "identity", bool(profile.user.first_name)),
            ("last_name", "Ajoutez votre nom", "identity", bool(profile.user.last_name)),
            ("headline", "Ajoutez un titre professionnel", "identity", bool(profile.headline)),
            ("bio", "Ajoutez une présentation", "identity", bool(profile.bio)),
            ("hourly_rate", "Ajoutez un tarif horaire", "pricing", profile.hourly_rate is not None),
            ("subjects", "Sélectionnez une matière", "offer", profile.subjects.exists()),
            ("levels", "Sélectionnez un niveau", "offer", profile.levels.exists()),
            (
                "teaching_modes",
                "Sélectionnez un mode d'enseignement",
                "offer",
                profile.teaching_modes.exists(),
            ),
            (
                "service_areas",
                "Sélectionnez une zone d'intervention",
                "offer",
                profile.service_areas.exists(),
            ),
        )
        return [
            {"code": code, "label": label, "section": section}
            for code, label, section, complete in checks
            if not complete
        ]


class AvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Availability
        fields = ("id", "weekday", "start_time", "end_time")
        read_only_fields = ("id",)

    def validate(self, attrs):
        if attrs["end_time"] <= attrs["start_time"]:
            raise serializers.ValidationError(
                {"end_time": "L'heure de fin doit être postérieure à l'heure de début."}
            )
        teacher = self.context["request"].user.teacher_profile
        queryset = Availability.objects.filter(teacher=teacher, weekday=attrs["weekday"])
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.filter(
            start_time__lt=attrs["end_time"], end_time__gt=attrs["start_time"]
        ).exists():
            raise serializers.ValidationError(
                {"weekday": "Un créneau existe déjà sur cette période."}
            )
        return attrs


class TeacherSearchSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.get_full_name", read_only=True)
    subjects = serializers.StringRelatedField(many=True)
    levels = serializers.StringRelatedField(many=True)
    teaching_modes = serializers.StringRelatedField(many=True)
    service_areas = serializers.StringRelatedField(many=True)
    url = serializers.CharField(source="get_absolute_url", read_only=True)
    public_profile = serializers.SerializerMethodField()

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
            "public_profile",
        )

    def get_public_profile(self, profile):
        from verification.models import ProfessionalCredential

        return {
            "verified_email": profile.user.email_verified,
            "verified_identity": IdentityVerification.objects.filter(
                user=profile.user, status=VerificationStatus.APPROVED
            ).exists(),
            "verified_phone": profile.user.phone_verified,
            "verified_diploma": ProfessionalCredential.objects.filter(
                user=profile.user,
                credential_type=ProfessionalCredential.CredentialType.DIPLOMA,
                status=VerificationStatus.APPROVED,
            ).exists(),
            "trust_score": getattr(profile.trust_score_snapshots.first(), "score", None),
            "has_availability": profile.availabilities.exists(),
        }


class LearnerProfileSerializer(serializers.ModelSerializer):
    user = TeacherProfileUserSerializer(read_only=True)
    first_name = serializers.CharField(
        source="user.first_name", write_only=True, required=False, max_length=150
    )
    last_name = serializers.CharField(
        source="user.last_name", write_only=True, required=False, max_length=150
    )
    levels = TeacherProfileReferenceSerializer(many=True, read_only=True)
    interests = TeacherProfileReferenceSerializer(many=True, read_only=True)
    preferred_service_area = TeacherProfileReferenceSerializer(read_only=True)

    level_ids = serializers.PrimaryKeyRelatedField(
        source="levels",
        queryset=Level.objects.filter(is_active=True),
        many=True,
        write_only=True,
        required=False,
    )
    interest_ids = serializers.PrimaryKeyRelatedField(
        source="interests",
        queryset=Subject.objects.filter(is_active=True),
        many=True,
        write_only=True,
        required=False,
    )
    preferred_service_area_id = serializers.PrimaryKeyRelatedField(
        source="preferred_service_area",
        queryset=ServiceArea.objects.filter(is_active=True),
        write_only=True,
        required=False,
        allow_null=True,
    )
    completion_percentage = serializers.IntegerField(read_only=True)

    class Meta:
        model = LearnerProfile
        fields = (
            "id",
            "user",
            "first_name",
            "last_name",
            "levels",
            "interests",
            "preferred_service_area",
            "level_ids",
            "interest_ids",
            "preferred_service_area_id",
            "completion_percentage",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "user",
            "levels",
            "interests",
            "preferred_service_area",
            "completion_percentage",
            "created_at",
            "updated_at",
        )

    def update(self, instance, validated_data):
        relation_data = {
            field: validated_data.pop(field)
            for field in ("levels", "interests")
            if field in validated_data
        }
        user_data = validated_data.pop("user", {})
        user = instance.user
        for field, value in user_data.items():
            setattr(user, field, value)
        if user_data:
            user.save(update_fields=(*user_data.keys(), "updated_at"))
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        for field, value in relation_data.items():
            getattr(instance, field).set(value)
        return instance
