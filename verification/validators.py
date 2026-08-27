from pathlib import Path

from django.core.exceptions import ValidationError

ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
ALLOWED_DOCUMENT_CONTENT_TYPES = {"application/pdf", "image/jpeg", "image/png"}
MAX_DOCUMENT_SIZE = 5 * 1024 * 1024


def validate_document(file):
    extension = Path(file.name).suffix.lower()
    if extension not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise ValidationError("Formats acceptés : PDF, JPEG et PNG.")
    if getattr(file, "content_type", None) not in ALLOWED_DOCUMENT_CONTENT_TYPES:
        raise ValidationError("Le type MIME du fichier n'est pas accepté.")
    if file.size > MAX_DOCUMENT_SIZE:
        raise ValidationError("Le fichier ne doit pas dépasser 5 Mo.")
