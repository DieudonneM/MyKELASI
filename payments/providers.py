import hmac
from dataclasses import dataclass
from hashlib import sha256
from typing import Protocol


@dataclass(frozen=True)
class PaymentInitiation:
    provider_reference: str


class PaymentProvider(Protocol):
    code: str

    def initiate(self, *, reference, amount, currency) -> PaymentInitiation: ...


class SandboxPaymentProvider:
    code = "sandbox"

    def initiate(self, *, reference, amount, currency):
        return PaymentInitiation(provider_reference=f"sandbox-{reference}")


def sign_webhook_payload(payload, secret):
    return hmac.new(str(secret).encode(), payload, sha256).hexdigest()


def verify_webhook_signature(payload, signature, secret):
    expected = sign_webhook_payload(payload, secret)
    return hmac.compare_digest(expected, signature or "")


def get_payment_provider(code):
    if code == SandboxPaymentProvider.code:
        return SandboxPaymentProvider()
    raise ValueError("Prestataire de paiement inconnu.")
