from django.db import transaction

from .models import IdentityVerification, ProfessionalCredential, VerificationUpload


@transaction.atomic
def purge_user_private_documents(user):
    for model, field_name in (
        (IdentityVerification, "document"),
        (ProfessionalCredential, "document"),
        (VerificationUpload, "chunk_file"),
    ):
        for item in model.objects.select_for_update().filter(user=user):
            getattr(item, field_name).delete(save=False)
            item.delete()
