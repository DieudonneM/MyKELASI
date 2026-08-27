import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient

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


@pytest.mark.django_db
def test_teacher_can_upload_and_list_private_verification_document(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    user = get_user_model().objects.create_user(
        email="teacher@example.com", password="Strong-password-2026", account_type="TEACHER"
    )
    client = APIClient()
    client.force_authenticate(user)
    upload = SimpleUploadedFile("passport.pdf", b"%PDF-1.4 test", content_type="application/pdf")

    response = client.post(
        "/api/v1/teacher/verifications/",
        {"document_type": "passport", "document": upload},
        format="multipart",
    )

    assert response.status_code == 201, response.data
    assert response.data["status"] == "pending"
    assert response.data["file_name"].endswith(".pdf")
    listing = client.get("/api/v1/teacher/verifications/")
    assert listing.status_code == 200
    assert len(listing.data["results"]) == 1


@pytest.mark.django_db
def test_verification_upload_rejects_wrong_mime_and_non_teacher():
    user_model = get_user_model()
    learner = user_model.objects.create_user(email="learner@example.com", account_type="LEARNER")
    client = APIClient()
    client.force_authenticate(learner)
    assert client.get("/api/v1/teacher/verifications/").status_code == 403

    teacher = user_model.objects.create_user(email="mime@example.com", account_type="TEACHER")
    client.force_authenticate(teacher)
    upload = SimpleUploadedFile("passport.pdf", b"not-a-pdf", content_type="text/plain")
    response = client.post(
        "/api/v1/teacher/verifications/",
        {"document_type": "passport", "document": upload},
        format="multipart",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_verification_reviewer_audits_rejection_reason(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    user_model = get_user_model()
    owner = user_model.objects.create_user(email="owner-review@example.com", account_type="TEACHER")
    reviewer = user_model.objects.create_user(email="reviewer-api@example.com")
    reviewer.groups.add(reviewer.groups.model.objects.get(name="VERIFICATION"))
    item = IdentityVerification.objects.create(
        user=owner,
        document_type="PASSPORT",
        document=SimpleUploadedFile(
            "passport.pdf", b"%PDF-1.4 test", content_type="application/pdf"
        ),
    )
    client = APIClient()
    client.force_authenticate(reviewer)
    response = client.post(
        f"/api/v1/verification/identity/{item.pk}/review/",
        {"status": "REJECTED", "rejection_reason": "Photo illisible"},
        format="json",
    )
    item.refresh_from_db()
    assert response.status_code == 200
    assert item.status == "REJECTED"
    assert item.reviewed_by_id == reviewer.pk
    assert item.reviewed_at is not None


@pytest.mark.django_db
def test_verification_upload_resumes_from_server_offset(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    user = get_user_model().objects.create_user(email="resume@example.com", account_type="TEACHER")
    client = APIClient()
    client.force_authenticate(user)
    init = client.post(
        "/api/v1/teacher/verifications/upload/",
        {"document_type": "passport", "file_name": "passport.pdf", "file_size": 9},
        format="json",
    )
    assert init.status_code == 201
    upload_id = init.data["upload_id"]
    first = client.patch(
        f"/api/v1/teacher/verifications/upload/{upload_id}/",
        {"chunk": SimpleUploadedFile("part", b"%PDF-1.4", content_type="application/pdf")},
        format="multipart",
        HTTP_UPLOAD_OFFSET="0",
    )
    assert first.status_code == 200
    assert first.data["offset"] == 8
    progress = client.get(f"/api/v1/teacher/verifications/upload/{upload_id}/")
    assert progress.data["offset"] == 8
