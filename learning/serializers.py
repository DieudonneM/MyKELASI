from django.utils import timezone
from rest_framework import serializers

from profiles.models import Level, ServiceArea, Subject, TeachingMode
from profiles.serializers import TeacherProfileReferenceSerializer

from .models import LearningRequest, MatchResult, Proposal


class LearningRequestSerializer(serializers.ModelSerializer):
    subject = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.filter(is_active=True)
    )
    level = serializers.PrimaryKeyRelatedField(
        queryset=Level.objects.filter(is_active=True)
    )
    teaching_mode = serializers.PrimaryKeyRelatedField(
        queryset=TeachingMode.objects.filter(is_active=True)
    )
    service_area = serializers.PrimaryKeyRelatedField(
        queryset=ServiceArea.objects.filter(is_active=True),
        allow_null=True,
        required=False,
    )
    def validate(self, attrs):
        preferred_date = attrs.get(
            "preferred_date",
            self.instance.preferred_date if self.instance else None,
        )
        preferred_start_time = attrs.get(
            "preferred_start_time",
            self.instance.preferred_start_time if self.instance else None,
        )
        if bool(preferred_date) != bool(preferred_start_time):
            raise serializers.ValidationError(
                {
                    "preferred_date": "La date et l'heure souhaitées doivent être renseignées ensemble.",
                    "preferred_start_time": "La date et l'heure souhaitées doivent être renseignées ensemble.",
                }
            )
        if preferred_date and preferred_date < timezone.localdate():
            raise serializers.ValidationError(
                {"preferred_date": "La date souhaitée ne peut pas être passée."}
            )
        return attrs

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
    teacher_rate = serializers.DecimalField(
        source="teacher.hourly_rate", max_digits=12, decimal_places=2, read_only=True
    )
    teacher_currency = serializers.CharField(source="teacher.currency", read_only=True)
    teacher_subjects = serializers.StringRelatedField(
        source="teacher.subjects", many=True, read_only=True
    )
    teacher_levels = serializers.StringRelatedField(
        source="teacher.levels", many=True, read_only=True
    )
    teacher_modes = serializers.StringRelatedField(
        source="teacher.teaching_modes", many=True, read_only=True
    )
    teacher_areas = serializers.StringRelatedField(
        source="teacher.service_areas", many=True, read_only=True
    )
    has_availability = serializers.SerializerMethodField()
    verification = serializers.SerializerMethodField()

    class Meta:
        model = MatchResult
        fields = (
            "teacher_id", "teacher_name", "teacher_url", "score", "reasons",
            "teacher_rate", "teacher_currency", "teacher_subjects", "teacher_levels",
            "teacher_modes", "teacher_areas", "has_availability", "verification",
        )

    def get_has_availability(self, match):
        return match.teacher.availabilities.exists()

    def get_verification(self, match):
        from verification.models import IdentityVerification, VerificationStatus
        from verification.models import ProfessionalCredential

        user = match.teacher.user
        return {
            "email": user.email_verified,
            "phone": user.phone_verified,
            "identity": IdentityVerification.objects.filter(
                user=user, status=VerificationStatus.APPROVED
            ).exists(),
            "diploma": ProfessionalCredential.objects.filter(
                user=user,
                credential_type=ProfessionalCredential.CredentialType.DIPLOMA,
                status=VerificationStatus.APPROVED,
            ).exists(),
        }


class ProposalSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    request_id = serializers.IntegerField(source="learning_request_id", read_only=True)
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False
    )
    teacher_name = serializers.CharField(source="teacher.user.get_full_name", read_only=True)
    hourly_rate = serializers.DecimalField(
        source="amount", max_digits=12, decimal_places=2, write_only=True, required=False
    )

    def to_internal_value(self, data):
        data = data.copy()
        if "amount" in data and "hourly_rate" not in data:
            data["hourly_rate"] = data["amount"]
        return super().to_internal_value(data)

    def validate(self, attrs):
        if "amount" not in attrs:
            raise serializers.ValidationError({"amount": "Le montant est requis."})
        return attrs

    class Meta:
        model = Proposal
        fields = (
            "id", "request_id", "public_id", "teacher_name", "amount", "hourly_rate", "message",
            "availability", "status", "created_at",
        )
        read_only_fields = ("public_id", "teacher_name", "status", "created_at")


class TeacherMatchedRequestSerializer(serializers.ModelSerializer):
    subject = TeacherProfileReferenceSerializer(read_only=True)
    level = TeacherProfileReferenceSerializer(read_only=True)
    teaching_mode = TeacherProfileReferenceSerializer(read_only=True)
    student = serializers.SerializerMethodField()
    budget = serializers.DecimalField(source="budget_max", max_digits=12, decimal_places=2)
    match_reasons = serializers.SerializerMethodField()
    timezone = serializers.CharField(default="Africa/Kinshasa")

    def get_student(self, obj):
        return {
            "id": obj.learner_id,
            "first_name": obj.learner.first_name,
            "last_name": obj.learner.last_name,
            "city": obj.service_area.name if obj.service_area else "Kinshasa",
        }

    def get_match_reasons(self, obj):
        match = obj.matches.filter(teacher__user=self.context["request"].user).first()
        return (
            [{"code": f"reason_{index}", "label": reason} for index, reason in enumerate(match.reasons)]
            if match
            else []
        )

    class Meta:
        model = LearningRequest
        fields = ("id", "subject", "level", "teaching_mode", "student", "budget", "status", "timezone", "match_reasons")
        read_only_fields = fields
