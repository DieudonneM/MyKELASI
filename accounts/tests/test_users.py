import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import IntegrityError
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.roles import INTERNAL_ROLE_NAMES


@pytest.mark.django_db
def test_user_uses_normalized_email_as_identifier():
    user_model = get_user_model()

    user = user_model.objects.create_user(
        email="APPRENANT@EXAMPLE.COM",
        password="test-password",
        account_type=user_model.AccountType.LEARNER,
    )

    assert user.email == "apprenant@example.com"
    assert user.check_password("test-password")
    assert user.username is None


@pytest.mark.django_db
def test_email_is_unique_case_insensitively_through_manager():
    user_model = get_user_model()
    user_model.objects.create_user(email="unique@example.com", password="test-password")

    with pytest.raises(IntegrityError):
        user_model.objects.create_user(email="UNIQUE@EXAMPLE.COM", password="test-password")


@pytest.mark.django_db
def test_superuser_has_required_permissions():
    user = get_user_model().objects.create_superuser(
        email="admin@example.com",
        password="test-password",
    )

    assert user.is_staff is True
    assert user.is_superuser is True
    assert user.email_verified is True
    assert user.account_type == ""


@pytest.mark.django_db
def test_internal_roles_exist_without_implicit_permissions():
    groups = Group.objects.filter(name__in=INTERNAL_ROLE_NAMES)

    assert set(groups.values_list("name", flat=True)) == set(INTERNAL_ROLE_NAMES)
    assert all(group.permissions.count() == 0 for group in groups)


@pytest.mark.django_db
def test_regular_user_cannot_access_another_account_in_admin(client):
    user_model = get_user_model()
    learner = user_model.objects.create_user(
        email="learner@example.com",
        password="test-password",
        account_type=user_model.AccountType.LEARNER,
    )
    other_user = user_model.objects.create_user(
        email="other@example.com",
        password="test-password",
        account_type=user_model.AccountType.TEACHER,
    )
    client.force_login(learner)

    response = client.get(reverse("admin:accounts_user_change", args=[other_user.pk]))

    assert response.status_code == 302
    assert response.url.startswith(reverse("admin:login"))


@pytest.mark.django_db
def test_superuser_can_open_user_admin(client):
    admin_user = get_user_model().objects.create_superuser(
        email="admin@example.com",
        password="test-password",
    )
    client.force_login(admin_user)

    response = client.get(reverse("admin:accounts_user_add"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_support_dashboard_excludes_internal_and_financial_data():
    user_model = get_user_model()
    support = user_model.objects.create_user(email="support@example.com", password="test-password")
    support.groups.add(Group.objects.get(name="SUPPORT"))
    user_model.objects.create_user(email="public@example.com", account_type="LEARNER")
    user_model.objects.create_user(email="internal@example.com", is_internal=True)
    client = APIClient()
    client.force_authenticate(support)

    response = client.get(reverse("accounts-api:support-dashboard"))

    assert response.status_code == 200
    assert {item["email"] for item in response.data["users"]} == {"public@example.com"}
    assert "amount" not in str(response.data)


@pytest.mark.django_db
def test_internal_dashboard_requires_internal_role(client):
    user = get_user_model().objects.create_user(
        email="public@example.com",
        password="test-password",
        account_type="LEARNER",
    )
    client.force_login(user)

    response = client.get(reverse("accounts:internal-dashboard"))

    assert response.status_code == 403


@pytest.mark.django_db
def test_internal_dashboard_accessible_to_support(client):
    support = get_user_model().objects.create_user(
        email="support@example.com",
        password="test-password",
        is_internal=True,
    )
    support.groups.add(Group.objects.get(name="SUPPORT"))
    client.force_login(support)

    response = client.get(reverse("accounts:internal-dashboard"))

    assert response.status_code == 200
    assert "Dashboard opérationnel" in response.content.decode()


@pytest.mark.django_db
def test_referentials_dashboard_requires_admin(client):
    support = get_user_model().objects.create_user(
        email="support@example.com",
        password="test-password",
        is_internal=True,
    )
    support.groups.add(Group.objects.get(name="SUPPORT"))
    client.force_login(support)

    response = client.get(reverse("accounts:referentials-dashboard"))

    assert response.status_code == 403


@pytest.mark.django_db
def test_referentials_dashboard_accessible_to_admin(client):
    admin = get_user_model().objects.create_user(
        email="admin@example.com",
        password="test-password",
        is_internal=True,
    )
    admin.groups.add(Group.objects.get(name="ADMIN"))
    client.force_login(admin)

    response = client.get(reverse("accounts:referentials-dashboard"))

    assert response.status_code == 200
    assert "Référentiels" in response.content.decode()
