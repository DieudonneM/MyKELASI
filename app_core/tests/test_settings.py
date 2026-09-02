import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    ("environment", "expected_debug"),
    (("development", "True"), ("staging", "False"), ("production", "False")),
)
def test_environment_loads_expected_debug_mode(environment, expected_debug):
    project_root = Path(__file__).resolve().parents[2]
    command = [
        sys.executable,
        "-c",
        "import django; django.setup(); from django.conf import settings; print(settings.DEBUG)",
    ]
    environment_variables = os.environ.copy()
    environment_variables["DJANGO_SETTINGS_MODULE"] = "app_core.settings"
    environment_variables["DJANGO_ENV"] = environment
    environment_variables["DJANGO_DEBUG"] = expected_debug
    result = subprocess.run(
        command,
        cwd=project_root,
        env=environment_variables,
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout.strip() == expected_debug


def test_development_allows_the_configured_mobile_lan_host():
    project_root = Path(__file__).resolve().parents[2]
    command = [
        sys.executable,
        "-c",
        "import django; django.setup(); from django.conf import settings; print('10.226.19.132' in settings.ALLOWED_HOSTS)",
    ]
    environment_variables = os.environ.copy()
    environment_variables["DJANGO_SETTINGS_MODULE"] = "app_core.settings"
    environment_variables["DJANGO_ENV"] = "development"
    environment_variables["DJANGO_ALLOWED_HOSTS"] = "10.226.19.132"
    result = subprocess.run(
        command,
        cwd=project_root,
        env=environment_variables,
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout.strip() == "True"


def test_private_media_root_is_not_public_media_root(settings):
    assert settings.PRIVATE_MEDIA_ROOT.resolve() != settings.MEDIA_ROOT.resolve()


def test_test_environment_disables_api_rate_limiting(settings):
    assert settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] == {
        "auth": None,
        "messages": None,
        "reports": None,
    }


@pytest.mark.parametrize("environment", ("staging", "production"))
def test_deployment_environments_enable_https_security(environment):
    project_root = Path(__file__).resolve().parents[2]
    command = [
        sys.executable,
        "-c",
        (
            "import django; django.setup(); from django.conf import settings; "
            "print(settings.SECURE_SSL_REDIRECT, settings.SECURE_HSTS_SECONDS, "
            "settings.SESSION_COOKIE_SECURE, settings.CSRF_COOKIE_SECURE)"
        ),
    ]
    environment_variables = os.environ.copy()
    environment_variables["DJANGO_SETTINGS_MODULE"] = "app_core.settings"
    environment_variables.update(
        {
            "DJANGO_ENV": environment,
            "DJANGO_SECURE_HSTS_SECONDS": "31536000",
        }
    )
    result = subprocess.run(
        command,
        cwd=project_root,
        env=environment_variables,
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout.strip() == "True 31536000 True True"


@pytest.mark.parametrize("hsts_seconds", ("0", "-1"))
def test_deployment_environments_reject_non_positive_hsts(hsts_seconds):
    project_root = Path(__file__).resolve().parents[2]
    command = [sys.executable, "-c", "import django; django.setup()"]
    environment_variables = os.environ.copy()
    environment_variables["DJANGO_SETTINGS_MODULE"] = "app_core.settings"
    environment_variables.update(
        {
            "DJANGO_ENV": "staging",
            "DJANGO_SECURE_HSTS_SECONDS": hsts_seconds,
        }
    )
    result = subprocess.run(
        command,
        cwd=project_root,
        env=environment_variables,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "DJANGO_SECURE_HSTS_SECONDS doit être strictement positif" in result.stderr
