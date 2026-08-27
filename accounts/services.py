from django.conf import settings
from django.contrib.auth.models import Group
from django.core.mail import send_mail
from django.urls import reverse

from .models import AuditLog, User
from .tokens import make_email_verification_token


def create_internal_user(*, email, password, role, **fields):
    if role not in {"SUPPORT", "VERIFICATION", "FINANCE", "MODERATION", "ADMIN", "SUPER_ADMIN"}:
        raise ValueError("Rôle interne inconnu.")
    user = User.objects.create_user(email=email, password=password, is_internal=True, **fields)
    user.groups.add(Group.objects.get(name=role))
    return user


def record_audit(*, actor, action, target, metadata=None):
    return AuditLog.objects.create(
        actor=actor,
        action=action,
        target_type=target.__class__.__name__,
        target_id=str(getattr(target, "public_id", target.pk)),
        metadata=metadata or {},
    )


def send_verification_email(user, request):
    token = make_email_verification_token(user)
    verification_url = request.build_absolute_uri(
        reverse("accounts:verify-email", kwargs={"token": token})
    )
    send_mail(
        subject="Vérifiez votre adresse email MyKELASI",
        message=(
            f"Bonjour {user.first_name or 'et bienvenue'},\n\n"
            "Vérifiez votre adresse email en ouvrant ce lien :\n"
            f"{verification_url}\n\n"
            "Ce lien expire dans 24 heures."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
