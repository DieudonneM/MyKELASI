from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import AuditLog
from notifications.models import Notification
from verification.models import IdentityVerification, VerificationDecision, VerificationStatus
from verification.validators import validate_document


@pytest.fixture(autouse=True)
def private_media_root(settings, tmp_path):
    settings.PRIVATE_MEDIA_ROOT = tmp_path / "private-media"


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
    assert response["Cache-Control"] == "private, no-store"
    assert response["X-Content-Type-Options"] == "nosniff"
    response.close()

    assert verification.document.storage.location == str(settings.PRIVATE_MEDIA_ROOT)
    assert verification.document.storage.location != str(settings.MEDIA_ROOT)
    assert client.get(f"/media/{verification.document.name}").status_code == 404


@pytest.mark.django_db
def test_private_document_access_is_revoked_after_expiration_suspension_and_deletion(client):
    user_model = get_user_model()
    owner = user_model.objects.create_user(email="lifecycle@example.com", account_type="TEACHER")
    document = IdentityVerification.objects.create(
        user=owner,
        document_type="PASSPORT",
        document=SimpleUploadedFile(
            "passport.pdf", b"%PDF-1.4 test", content_type="application/pdf"
        ),
    )
    url = reverse("verification:private-document", args=("identity", document.pk))
    client.force_login(owner)

    document.status = VerificationStatus.EXPIRED
    document.save(update_fields=("status",))
    assert client.get(url).status_code == 404

    document.status = VerificationStatus.PENDING
    document.save(update_fields=("status",))
    owner.status = user_model.Status.SUSPENDED
    owner.save(update_fields=("status",))
    assert client.get(url).status_code == 403

    owner.status = user_model.Status.ACTIVE
    owner.save(update_fields=("status",))
    document.delete()
    assert client.get(url).status_code == 404


@pytest.mark.django_db
def test_account_deactivation_purges_private_documents(client):
    user_model = get_user_model()
    owner = user_model.objects.create_user(email="deactivate@example.com", account_type="TEACHER")
    document = IdentityVerification.objects.create(
        user=owner,
        document_type="PASSPORT",
        document=SimpleUploadedFile(
            "passport.pdf", b"%PDF-1.4 test", content_type="application/pdf"
        ),
    )
    document_path = document.document.path
    client.force_login(owner)

    response = client.post(reverse("accounts:deactivate"))

    owner.refresh_from_db()
    assert response.status_code == 302
    assert owner.status == user_model.Status.DEACTIVATED
    assert not IdentityVerification.objects.filter(pk=document.pk).exists()
    assert not Path(document_path).exists()


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
def test_verification_queue_review_is_notifiable_and_immutable(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    user_model = get_user_model()
    owner = user_model.objects.create_user(email="queue-owner@example.com", account_type="TEACHER")
    reviewer = user_model.objects.create_user(email="queue-reviewer@example.com", is_staff=True)
    reviewer.groups.add(reviewer.groups.model.objects.get(name="VERIFICATION"))
    document = IdentityVerification.objects.create(
        user=owner,
        document_type="PASSPORT",
        document=SimpleUploadedFile(
            "passport.pdf", b"%PDF-1.4 test", content_type="application/pdf"
        ),
    )
    client = APIClient()
    client.force_authenticate(reviewer)

    queue = client.get(reverse("verification-queue"))
    assert queue.status_code == 200
    assert queue.data["results"][0]["id"] == document.pk
    response = client.post(
        reverse("verification-review", args=("identity", document.pk)),
        {"status": VerificationStatus.REJECTED, "rejection_reason": "Document illisible."},
        format="json",
    )

    assert response.status_code == 200
    assert VerificationDecision.objects.filter(
        document_id=document.pk, to_status=VerificationStatus.REJECTED
    ).exists()
    assert Notification.objects.filter(
        user=owner, kind=Notification.Kind.VERIFICATION_UPDATED
    ).exists()
    audit = AuditLog.objects.get(action="verification.review")
    with pytest.raises(ValueError, match="immuable"):
        audit.save()


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
    assert "document" not in response.data
    assert "/media/" not in str(response.data)
    listing = client.get("/api/v1/teacher/verifications/")
    assert listing.status_code == 200
    assert len(listing.data["results"]) == 1
    assert "document" not in listing.data["results"][0]


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


def test_document_validator_rejects_large_incoherent_and_corrupted_files():
    oversized = SimpleUploadedFile(
        "passport.pdf",
        b"%PDF-" + b"x" * (5 * 1024 * 1024),
        content_type="application/pdf",
    )
    incoherent = SimpleUploadedFile("passport.pdf", b"%PDF-1.4", content_type="image/png")
    corrupted = SimpleUploadedFile("passport.pdf", b"not a PDF", content_type="application/pdf")

    for upload in (oversized, incoherent, corrupted):
        with pytest.raises(ValidationError):
            validate_document(upload)


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
def test_verification_review_requires_reason_and_cannot_be_replayed(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    user_model = get_user_model()
    owner = user_model.objects.create_user(
        email="transition-owner@example.com", account_type="TEACHER"
    )
    reviewer = user_model.objects.create_user(email="transition-reviewer@example.com")
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
    endpoint = f"/api/v1/verification/identity/{item.pk}/review/"

    assert client.post(endpoint, {"status": "APPROVED"}, format="json").status_code == 400
    assert (
        client.post(
            endpoint,
            {"status": "APPROVED", "rejection_reason": "Document conforme."},
            format="json",
        ).status_code
        == 200
    )
    assert (
        client.post(
            endpoint,
            {"status": "EXPIRED", "rejection_reason": "Tentative de rejeu."},
            format="json",
        ).status_code
        == 409
    )
    assert VerificationDecision.objects.filter(document_id=item.pk).count() == 1


@pytest.mark.django_db
def test_verification_document_and_history_api_are_private_and_audited(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    user_model = get_user_model()
    owner = user_model.objects.create_user(
        email="private-owner@example.com", account_type="TEACHER"
    )
    reviewer = user_model.objects.create_user(email="private-reviewer@example.com")
    reviewer.groups.add(reviewer.groups.model.objects.get(name="VERIFICATION"))
    item = IdentityVerification.objects.create(
        user=owner,
        document_type="PASSPORT",
        document=SimpleUploadedFile(
            "passport.pdf", b"%PDF-1.4 test", content_type="application/pdf"
        ),
    )
    VerificationDecision.objects.create(
        document_type="identity",
        document_id=item.pk,
        reviewer=reviewer,
        from_status="PENDING",
        to_status="REJECTED",
        reason="Document illisible.",
    )
    client = APIClient()
    document_endpoint = f"/api/v1/verification/identity/{item.pk}/document/"
    history_endpoint = f"/api/v1/verification/identity/{item.pk}/history/"

    assert client.get(document_endpoint).status_code == 403
    client.force_authenticate(reviewer)
    response = client.get(document_endpoint)
    assert response.status_code == 200
    assert response["Cache-Control"] == "private, no-store"
    assert response["X-Content-Type-Options"] == "nosniff"
    response.close()
    history = client.get(history_endpoint)
    assert history.status_code == 200
    assert history.data["results"][0]["reason"] == "Document illisible."
    assert AuditLog.objects.filter(actor=reviewer, action="verification.document_view").exists()
    assert AuditLog.objects.filter(actor=reviewer, action="verification.history_view").exists()


@pytest.mark.django_db
def test_teacher_can_submit_a_replacement_after_rejection(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    user_model = get_user_model()
    teacher = user_model.objects.create_user(
        email="replacement@example.com", account_type="TEACHER"
    )
    previous = IdentityVerification.objects.create(
        user=teacher,
        document_type="PASSPORT",
        status=VerificationStatus.REJECTED,
        rejection_reason="Document illisible.",
        document=SimpleUploadedFile(
            "old-passport.pdf", b"%PDF-1.4 test", content_type="application/pdf"
        ),
    )
    client = APIClient()
    client.force_authenticate(teacher)
    response = client.post(
        "/api/v1/teacher/verifications/",
        {
            "document_type": "passport",
            "document": SimpleUploadedFile(
                "new-passport.pdf", b"%PDF-1.4 test", content_type="application/pdf"
            ),
        },
        format="multipart",
    )

    assert response.status_code == 201
    assert response.data["status"] == "pending"
    assert response.data["id"] != previous.pk


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
