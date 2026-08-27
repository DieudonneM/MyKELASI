import hashlib

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework.test import APIClient

from analytics.services import product_kpis, record_event
from learning.models import LearningRequest
from profiles.models import ConfigurationVersion, Level, ServiceArea, Subject, TeachingMode


@pytest.mark.django_db
def test_events_are_pseudonymized_and_kpis_use_server_data():
    user = get_user_model().objects.create_user(email="analytics@example.com", account_type="LEARNER")
    event = record_event(name="request.created", actor=user, context={"request_id": 4})
    LearningRequest.objects.create(
        learner=user,
        subject=Subject.objects.first(),
        level=Level.objects.first(),
        teaching_mode=TeachingMode.objects.first(),
        service_area=ServiceArea.objects.first(),
        budget_max=20000,
        description="Demande analytics.",
    )

    assert event.actor_hash
    assert event.actor_hash == hashlib.sha256(str(user.pk).encode()).hexdigest()
    assert str(user.pk) not in str(event.context)
    assert product_kpis()["requests"] == 1
    assert product_kpis()["north_star_completed_sessions"] == 0


@pytest.mark.django_db
def test_analytics_api_is_admin_only():
    user = get_user_model().objects.create_user(email="learner-analytics@example.com")
    client = APIClient()
    client.force_authenticate(user)
    assert client.get(reverse("analytics-api:dashboard")).status_code == 403

    user.groups.add(Group.objects.get(name="ADMIN"))
    assert client.get(reverse("analytics-api:dashboard")).status_code == 200


@pytest.mark.django_db
def test_configuration_versions_are_immutable():
    actor = get_user_model().objects.create_user(email="config-admin@example.com")
    config = ConfigurationVersion.objects.create(
        key="matching_weights",
        version=1,
        value={"subject": 20},
        created_by=actor,
    )
    with pytest.raises(ValueError, match="immuable"):
        config.save()
