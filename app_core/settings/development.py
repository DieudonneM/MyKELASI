from .base import *  # noqa: F403
from .base import env

DEBUG = env.bool("DJANGO_DEBUG", default=True)

if not ALLOWED_HOSTS:  # noqa: F405
    ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
