import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from verification.models import IdentityVerification
from verification.validators import validate_document


@pytest.mark.django_db
def test_document_is_private_to_owner(client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    user_model = get_user_model()
    owner = user_model.objects.create_user(
        email="owner@example.com",
        password="Strong-password-2026",
        account_type="TEACHER",
    )
    other = user_model.objects.create_user(
        email="other@example.com",
        password="Strong-password-2026",
        account_type="TEACHER",
    )
    verification = IdentityVerification.objects.create(
        user=owner,
        document_type="PASSPORT",
        document=SimpleUploadedFile(
            "passport.pdf", b"%PDF-1.4 test", content_type="application/pdf"
        ),
    )
    url = reverse("verification:private-document", args=("identity", verification.pk))

    client.force_login(other)
    assert client.get(url).status_code == 403

    client.force_login(owner)
    response = client.get(url)
    assert response.status_code == 200
    response.close()


@pytest.mark.django_db
def test_verification_group_can_review_document(client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    user_model = get_user_model()
    owner = user_model.objects.create_user(email="owner@example.com", account_type="TEACHER")
    reviewer = user_model.objects.create_user(
        email="reviewer@example.com",
        password="Strong-password-2026",
        is_staff=True,
    )
    reviewer.groups.add(reviewer.groups.model.objects.get(name="VERIFICATION"))
    verification = IdentityVerification.objects.create(
        user=owner,
        document_type="PASSPORT",
        document=SimpleUploadedFile(
            "passport.pdf", b"%PDF-1.4 test", content_type="application/pdf"
        ),
    )

    client.force_login(reviewer)
    response = client.get(
        reverse("verification:private-document", args=("identity", verification.pk))
    )

    assert response.status_code == 200
    response.close()


def test_document_validator_rejects_unsupported_extension():
    file = SimpleUploadedFile("malware.exe", b"not-safe")

    with pytest.raises(ValidationError):
        validate_document(file)
