from django.conf import settings
from django.core import signing

EMAIL_VERIFICATION_SALT = "accounts.email-verification"


def make_email_verification_token(user):
    return signing.dumps(
        {"user_id": user.pk, "email": user.email},
        salt=EMAIL_VERIFICATION_SALT,
        compress=True,
    )


def read_email_verification_token(token):
    return signing.loads(
        token,
        salt=EMAIL_VERIFICATION_SALT,
        max_age=settings.EMAIL_VERIFICATION_MAX_AGE,
    )
