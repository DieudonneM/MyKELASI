import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_health_endpoint(client):
    response = client.get(reverse("health"))

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
def test_api_root_is_versioned(client):
    response = client.get(reverse("api-root"))

    assert response.status_code == 200
    assert response.json() == {"name": "MyKELASI API", "version": "v1"}
