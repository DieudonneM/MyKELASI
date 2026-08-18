from pathlib import Path

from django.core.exceptions import ValidationError

ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_DOCUMENT_SIZE = 10 * 1024 * 1024


def validate_document(file):
    extension = Path(file.name).suffix.lower()
    if extension not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise ValidationError("Formats acceptés : PDF, JPEG et PNG.")
    if file.size > MAX_DOCUMENT_SIZE:
        raise ValidationError("Le fichier ne doit pas dépasser 10 Mo.")
