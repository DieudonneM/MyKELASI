from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse

from .tokens import make_email_verification_token


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
