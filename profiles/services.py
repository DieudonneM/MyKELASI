from django.conf import settings

from .models import ConfigurationVersion


def current_configuration(key, default):
    configuration = ConfigurationVersion.objects.filter(key=key).first()
    if configuration is None:
        return default
    return {**default, **configuration.value}


def matching_weights():
    return current_configuration("matching_weights", settings.MATCHING_WEIGHTS)


def payment_commission_rate():
    configuration = current_configuration(
        "payment_commission", {"rate": str(settings.PAYMENT_COMMISSION_RATE)}
    )
    return configuration["rate"]


def booking_currency():
    return current_configuration("currency", {"code": "CDF"})["code"]


def cancellation_policy():
    return current_configuration("policies", {}).get("cancellation")
