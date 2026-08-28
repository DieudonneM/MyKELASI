from rest_framework import serializers

from .models import ConfigurationVersion, Level, ServiceArea, Subject, TeachingMode


class SubjectAdminSerializer(serializers.ModelSerializer):
    code = serializers.SlugField(source="slug")

    class Meta:
        model = Subject
        fields = ("id", "name", "code", "is_active")


class LevelAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level
        fields = ("id", "name", "code", "order", "is_active")


class TeachingModeAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeachingMode
        fields = ("id", "name", "code", "is_active")


class ServiceAreaAdminSerializer(serializers.ModelSerializer):
    code = serializers.SlugField(source="slug")

    class Meta:
        model = ServiceArea
        fields = ("id", "name", "code", "is_active")


class ConfigurationVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfigurationVersion
        fields = ("id", "key", "version", "value", "created_at")
        read_only_fields = ("id", "version", "created_at")

    def validate_key(self, value):
        if value not in {"matching_weights", "payment_commission", "currency", "policies"}:
            raise serializers.ValidationError("Clé de configuration non prise en charge.")
        return value

    def validate(self, attrs):
        key = attrs["key"]
        value = attrs["value"]
        if key == "matching_weights" and (
            not value
            or not all(isinstance(weight, int) and weight >= 0 for weight in value.values())
        ):
            raise serializers.ValidationError(
                {"value": "Pondérations entières positives requises."}
            )
        if key == "payment_commission" and value.get("rate") not in {
            "0.00",
            "0.05",
            "0.10",
            "0.12",
            "0.15",
            "0.20",
        }:
            raise serializers.ValidationError({"value": "Taux de commission non autorisé."})
        if key == "currency" and value.get("code") != "CDF":
            raise serializers.ValidationError({"value": "La devise V1 est CDF."})
        if key == "policies" and not isinstance(value.get("cancellation"), str):
            raise serializers.ValidationError(
                {"value": "La politique d'annulation est obligatoire."}
            )
        return attrs
