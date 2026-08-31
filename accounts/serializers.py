from django.core import signing
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .mfa import confirm_device
from .models import MfaDevice, User
from .roles import INTERNAL_ROLE_NAMES
from .services import send_verification_email
from .tokens import read_email_verification_token


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "account_type",
            "password",
            "password_confirm",
        )

    def validate_email(self, value):
        email = value.strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("Un compte utilise déjà cette adresse email.")
        return email

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "Les mots de passe diffèrent."})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        send_verification_email(user, self.context["request"])
        return user


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    mfa_code = serializers.CharField(write_only=True, required=False)

    def validate(self, attrs):
        data = super().validate(attrs)
        if self.user.status != User.Status.ACTIVE:
            raise AuthenticationFailed("Ce compte n'est pas disponible.")
        if not self.user.email_verified:
            raise AuthenticationFailed("Vérifiez votre adresse email avant de vous connecter.")
        if self.user.is_internal:
            code = attrs.get("mfa_code")
            device = getattr(self.user, "mfa_device", None)
            if device is None:
                raise AuthenticationFailed("La configuration MFA de ce compte est requise.")
            if not confirm_device(user=self.user, code=code):
                raise AuthenticationFailed("Code MFA invalide.")
        from .services import record_audit

        record_audit(actor=self.user, action="auth.login", target=self.user)
        return data


class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.CharField()

    def save(self):
        try:
            payload = read_email_verification_token(self.validated_data["token"])
            user = User.objects.get(pk=payload["user_id"], email=payload["email"])
        except signing.BadSignature, signing.SignatureExpired, User.DoesNotExist, KeyError:
            raise serializers.ValidationError({"token": "Lien invalide ou expiré."}) from None

        if not user.email_verified:
            user.email_verified = True
            user.save(update_fields=("email_verified", "updated_at"))
            from notifications.models import Notification

            Notification.objects.create(
                user=user,
                kind=Notification.Kind.EMAIL_VERIFICATION,
                title="Adresse email vérifiée",
                body="Votre adresse email a été vérifiée avec succès.",
            )
        return user


class CurrentUserSerializer(serializers.ModelSerializer):
    internal_roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "account_type",
            "email_verified",
            "is_internal",
            "internal_roles",
        )
        read_only_fields = fields

    def get_internal_roles(self, user):
        if user.is_superuser:
            return list(INTERNAL_ROLE_NAMES)
        return list(
            user.groups.filter(name__in=INTERNAL_ROLE_NAMES)
            .order_by("name")
            .values_list("name", flat=True)
        )


class MfaCodeSerializer(serializers.Serializer):
    code = serializers.CharField(write_only=True, min_length=6, max_length=6)


class MfaDeviceSerializer(serializers.ModelSerializer):
    provisioning_uri = serializers.SerializerMethodField()

    class Meta:
        model = MfaDevice
        fields = ("confirmed_at", "provisioning_uri")
        read_only_fields = fields

    def get_provisioning_uri(self, obj):
        issuer = "MyKELASI"
        return f"otpauth://totp/{issuer}:{obj.user.email}?secret={obj.secret}&issuer={issuer}"
