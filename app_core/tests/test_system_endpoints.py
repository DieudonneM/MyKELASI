import pytest
from django.core import mail
from django.urls import reverse


@pytest.mark.django_db
def test_health_endpoint(client):
    response = client.get(reverse("health"))

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
def test_ready_endpoint(client):
    response = client.get(reverse("ready"))

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "connected"}


@pytest.mark.django_db
def test_openapi_schema_endpoint(client):
    response = client.get(reverse("openapi-schema"))

    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "MyKELASI API"
    assert len(schema["paths"]) >= 40
    assert schema["components"]["schemas"]["PaginatedResponse"]["required"] == [
        "count",
        "next",
        "previous",
        "results",
    ]
    assert schema["components"]["schemas"]["DecimalAmount"]["type"] == "string"


@pytest.mark.django_db
def test_api_root_is_versioned(client):
    response = client.get(reverse("api-root"))

    assert response.status_code == 200
    assert response.json() == {"name": "MyKELASI API", "version": "v1"}


@pytest.mark.django_db
def test_home_page_is_public(client):
    response = client.get(reverse("home"))

    assert response.status_code == 200
    assert "Trouver un enseignant" in response.content.decode()


@pytest.mark.django_db
def test_home_page_presents_learning_categories(client):
    response = client.get(reverse("home"))
    content = response.content.decode()

    assert "Explorez par objectif" in content
    assert "Langues et communication" in content
    assert "Numérique et création" in content


@pytest.mark.django_db
def test_home_page_requests_location_when_not_already_authorized(client):
    response = client.get(reverse("home"))

    assert "myKelasiRequestUserLocation" in response.content.decode()


@pytest.mark.django_db
def test_about_page_is_public(client):
    response = client.get(reverse("about"))

    assert response.status_code == 200
    assert "Rendre le bon enseignement accessible" in response.content.decode()


@pytest.mark.django_db
def test_contact_page_is_public(client):
    response = client.get(reverse("contact"))

    assert response.status_code == 200
    assert "Parlons de votre projet" in response.content.decode()


@pytest.mark.django_db
def test_contact_form_sends_email(client):
    response = client.post(
        reverse("contact"),
        {
            "name": "Marie Test",
            "email": "marie@example.com",
            "subject": "learner",
            "message": "Je souhaite trouver un enseignant de mathématiques.",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("contact")
    assert len(mail.outbox) == 1
    assert mail.outbox[0].reply_to == ["marie@example.com"]


@pytest.mark.django_db
def test_privacy_page_is_public(client):
    response = client.get(reverse("privacy"))

    assert response.status_code == 200
    assert "Politique de confidentialité" in response.content.decode()


@pytest.mark.django_db
def test_terms_page_is_public(client):
    response = client.get(reverse("terms"))

    assert response.status_code == 200
    assert "Conditions d'utilisation" in response.content.decode()


@pytest.mark.django_db
def test_academic_integrity_page_is_public(client):
    response = client.get(reverse("academic-integrity"))

    assert response.status_code == 200
    assert "Charte d'intégrité académique" in response.content.decode()


@pytest.mark.django_db
def test_footer_contains_legal_links(client):
    response = client.get(reverse("home"))
    content = response.content.decode()

    assert reverse("privacy") in content
    assert reverse("terms") in content
    assert reverse("academic-integrity") in content
    assert reverse("contact") in content
