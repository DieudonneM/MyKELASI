from django.urls import path

from .views import (
    IdentityVerificationCreateView,
    PrivateDocumentView,
    ProfessionalCredentialCreateView,
)

app_name = "verification"

urlpatterns = [
    path("identite/", IdentityVerificationCreateView.as_view(), name="identity-create"),
    path("qualification/", ProfessionalCredentialCreateView.as_view(), name="credential-create"),
    path("document/<str:kind>/<int:pk>/", PrivateDocumentView.as_view(), name="private-document"),
]
