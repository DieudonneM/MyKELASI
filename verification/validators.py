from pathlib import Path

from django.core.exceptions import ValidationError

ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_DOCUMENT_SIZE = 5 * 1024 * 1024
DOCUMENT_TYPES = {
    ".pdf": ("application/pdf", b"%PDF-"),
    ".jpg": ("image/jpeg", b"\xff\xd8\xff"),
    ".jpeg": ("image/jpeg", b"\xff\xd8\xff"),
    ".png": ("image/png", b"\x89PNG\r\n\x1a\n"),
}


def validate_document(file):
    extension = Path(file.name).suffix.lower()
    if extension not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise ValidationError("Formats acceptés : PDF, JPEG et PNG.")
    expected_content_type, signature = DOCUMENT_TYPES[extension]
    if getattr(file, "content_type", None) != expected_content_type:
        raise ValidationError("Le type MIME ne correspond pas à l'extension du fichier.")
    if file.size > MAX_DOCUMENT_SIZE:
        raise ValidationError("Le fichier ne doit pas dépasser 5 Mo.")
    initial_position = file.tell()
    header = file.read(len(signature))
    file.seek(initial_position)
    if header != signature:
        raise ValidationError("Le contenu du fichier est invalide ou corrompu.")
