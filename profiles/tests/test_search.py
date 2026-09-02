from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from profiles.models import Level, ServiceArea, Subject, TeachingMode


def create_teacher(email, name, rate, subject, area, *, is_public=True):
    user = get_user_model().objects.create_user(
        email=email,
        account_type="TEACHER",
        email_verified=True,
        first_name=name,
        last_name="Test",
    )
    profile = user.teacher_profile
    profile.headline = f"Enseignant de {subject.name}"
    profile.bio = "Accompagnement pédagogique personnalisé."
    profile.hourly_rate = Decimal(rate)
    profile.years_experience = 5
    profile.languages = "Français"
    profile.is_public = is_public
    profile.save()
    profile.subjects.add(subject)
    profile.levels.add(Level.objects.first())
    profile.teaching_modes.add(TeachingMode.objects.first())
    profile.service_areas.add(area)
    return profile


@pytest.mark.django_db
def test_web_search_filters_subject_area_and_budget(client):
    math = Subject.objects.get(slug="mathematiques")
    french = Subject.objects.get(slug="francais")
    gombe = ServiceArea.objects.get(slug="gombe")
    limete = ServiceArea.objects.get(slug="limete")
    expected = create_teacher("math@example.com", "Alice", "20000", math, gombe)
    create_teacher("french@example.com", "Bruno", "15000", french, gombe)
    create_teacher("expensive@example.com", "Chantal", "40000", math, limete)

    response = client.get(
        reverse("profiles:teacher-search"),
        {"subject": math.pk, "area": gombe.pk, "max_rate": 25000},
    )

    assert response.status_code == 200
    assert list(response.context["teachers"]) == [expected]


@pytest.mark.django_db
def test_web_search_filters_all_learning_criteria(client):
    subject = Subject.objects.get(slug="mathematiques")
    level = Level.objects.get(code="secondaire")
    mode = TeachingMode.objects.get(code="en-ligne")
    area = ServiceArea.objects.get(slug="gombe")
    expected = create_teacher("all-filters@example.com", "Alice", "20000", subject, area)
    expected.levels.set([level])
    expected.teaching_modes.set([mode])

    other_level = Level.objects.exclude(pk=level.pk).first()
    other_mode = TeachingMode.objects.exclude(pk=mode.pk).first()
    wrong_level = create_teacher("wrong-level@example.com", "Bruno", "10000", subject, area)
    wrong_level.levels.set([other_level])
    wrong_level.teaching_modes.set([mode])
    wrong_mode = create_teacher("wrong-mode@example.com", "Chantal", "10000", subject, area)
    wrong_mode.levels.set([level])
    wrong_mode.teaching_modes.set([other_mode])

    response = client.get(
        reverse("profiles:teacher-search"),
        {
            "subject": subject.pk,
            "level": level.pk,
            "mode": mode.pk,
            "area": area.pk,
            "max_rate": "20000.00",
        },
    )

    assert list(response.context["teachers"]) == [expected]


@pytest.mark.django_db
def test_search_excludes_private_and_inactive_profiles(client):
    subject = Subject.objects.first()
    area = ServiceArea.objects.first()
    public = create_teacher("public@example.com", "Public", "20000", subject, area)
    create_teacher("private@example.com", "Private", "18000", subject, area, is_public=False)
    inactive = create_teacher("inactive@example.com", "Inactive", "16000", subject, area)
    inactive.user.is_active = False
    inactive.user.save(update_fields=("is_active",))

    response = client.get(reverse("profiles:teacher-search"))

    assert list(response.context["teachers"]) == [public]


@pytest.mark.django_db
def test_web_search_orders_by_price(client):
    subject = Subject.objects.first()
    area = ServiceArea.objects.first()
    expensive = create_teacher("expensive@example.com", "Expensive", "30000", subject, area)
    affordable = create_teacher("affordable@example.com", "Affordable", "10000", subject, area)

    response = client.get(reverse("profiles:teacher-search"), {"ordering": "hourly_rate"})

    assert list(response.context["teachers"]) == [affordable, expensive]


@pytest.mark.django_db
def test_web_search_paginates_and_preserves_filters(client):
    subject = Subject.objects.first()
    area = ServiceArea.objects.first()
    for index in range(13):
        create_teacher(
            f"paged-{index}@example.com",
            f"Paged {index:02}",
            "20000",
            subject,
            area,
        )

    response = client.get(
        reverse("profiles:teacher-search"),
        {"subject": subject.pk, "area": area.pk, "ordering": "hourly_rate"},
    )

    assert response.status_code == 200
    assert response.context["paginator"].count == 13
    assert len(response.context["teachers"]) == 12
    assert response.context["is_paginated"] is True
    assert "subject=" in response.context["query_string"]
    assert "area=" in response.context["query_string"]
    assert "ordering=hourly_rate" in response.content.decode()
    assert 'aria-label="Page suivante"' in response.content.decode()


@pytest.mark.django_db
def test_api_search_is_public_filtered_and_paginated():
    subject = Subject.objects.get(slug="mathematiques")
    other_subject = Subject.objects.get(slug="francais")
    area = ServiceArea.objects.first()
    expected = create_teacher("api@example.com", "API", "12000", subject, area)
    create_teacher("other@example.com", "Other", "10000", other_subject, area)

    response = APIClient().get(
        reverse("profiles-api:teacher-search"),
        {"subject": subject.pk, "max_rate": 15000},
    )

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["public_id"] == str(expected.public_id)
    assert response.data["results"][0]["map_locations"] == [
        {
            "name": area.name,
            "latitude": None,
            "longitude": None,
        }
    ]


@pytest.mark.django_db
def test_text_search_matches_subject_name(client):
    subject = Subject.objects.get(slug="programmation")
    area = ServiceArea.objects.first()
    teacher = create_teacher("code@example.com", "Grace", "22000", subject, area)

    response = client.get(reverse("profiles:teacher-search"), {"q": "programmation"})

    assert list(response.context["teachers"]) == [teacher]


@pytest.mark.django_db
def test_api_search_paginates_twelve_teachers():
    subject = Subject.objects.first()
    area = ServiceArea.objects.first()
    for index in range(13):
        create_teacher(
            f"teacher-{index}@example.com",
            f"Teacher {index:02}",
            "20000",
            subject,
            area,
        )

    response = APIClient().get(reverse("profiles-api:teacher-search"))

    assert response.status_code == 200
    assert response.data["count"] == 13
    assert len(response.data["results"]) == 12
    assert response.data["next"] is not None


@pytest.mark.django_db
def test_api_teacher_detail_is_public_and_contains_only_public_fields():
    subject = Subject.objects.first()
    area = ServiceArea.objects.first()
    teacher = create_teacher("detail@example.com", "Detail", "20000", subject, area)

    response = APIClient().get(
        reverse("profiles-api:teacher-detail", kwargs={"public_id": teacher.public_id})
    )

    assert response.status_code == 200
    assert response.data["public_id"] == str(teacher.public_id)
    assert "email" not in response.data
    assert "phone_number" not in response.data
    assert response.data["public_profile"]["verified_email"] is True
