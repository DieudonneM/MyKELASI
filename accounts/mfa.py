import pyotp
from django.utils import timezone


def generate_secret():
    return pyotp.random_base32()


def totp_code(secret):
    return pyotp.TOTP(secret).now()


def confirm_device(*, user, code):
    device = getattr(user, "mfa_device", None)
    if device is None or not code or not code.isdigit() or len(code) != 6:
        return False

    if not pyotp.TOTP(device.secret).verify(code, valid_window=1):
        return False

    now = timezone.now()
    update_fields = ["last_verified_at"]
    device.last_verified_at = now
    if device.confirmed_at is None:
        device.confirmed_at = now
        update_fields.append("confirmed_at")
    device.save(update_fields=update_fields)
    return True
