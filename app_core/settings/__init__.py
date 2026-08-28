import os
from importlib import import_module

environment = os.getenv("DJANGO_ENV", "development")
settings_modules = {
    "development": "app_core.settings.development",
    "staging": "app_core.settings.staging",
    "test": "app_core.settings.test",
    "production": "app_core.settings.production",
}

if environment not in settings_modules:
    valid_environments = ", ".join(settings_modules)
    raise RuntimeError(
        f"DJANGO_ENV invalide: {environment}. Valeurs acceptées: {valid_environments}."
    )

settings = import_module(settings_modules[environment])

for setting_name in dir(settings):
    if setting_name.isupper():
        globals()[setting_name] = getattr(settings, setting_name)
