from django.contrib import admin

from .models import (
    Availability,
    LearnerProfile,
    Level,
    ServiceArea,
    Subject,
    TeacherProfile,
    TeachingMode,
)

PROFILE_MODELS = (
    Subject,
    Level,
    TeachingMode,
    ServiceArea,
    LearnerProfile,
    TeacherProfile,
    Availability,
)

for model in PROFILE_MODELS:
    admin.site.register(model)
