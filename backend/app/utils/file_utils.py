import hashlib
import io
import os
import re
import zipfile
from typing import Tuple
from app.core.config import settings
from app.core.exceptions import InvalidPDFException, FileTooLargeException


def compute_file_hash(file_bytes: bytes) -> str:
    """Compute SHA-256 hash of file content to detect duplicates."""
    sha256 = hashlib.sha256()
    sha256.update(file_bytes)
    return sha256.hexdigest()


def format_file_size(size_bytes: int) -> str:
    """Format bytes into readable string (e.g. 1.25 MB)."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal or invalid characters."""
    clean_name = os.path.basename(filename)
    clean_name = re.sub(r'[^a-zA-Z0-9_\-\. ]', '_', clean_name)
    return clean_name.strip() or "document.pdf"


def validate_pdf(filename: str, file_bytes: bytes, max_mb: int = settings.MAX_FILE_SIZE_MB) -> None:
    """
    Validate that the file:
    1. Is not empty (0 bytes).
    2. Does not exceed max_mb.
    3. Has .pdf extension.
    4. Starts with PDF magic bytes (%PDF).
    """
    if not file_bytes or len(file_bytes) == 0:
        raise InvalidPDFException(filename, "Uploaded file is 0 bytes / empty")

    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > max_mb:
        raise FileTooLargeException(filename, size_mb, max_mb)

    if not filename.lower().endswith(".pdf"):
        raise InvalidPDFException(filename, "File extension must be .pdf")

    # Magic bytes check: PDF header begins with %PDF- (hex: 25 50 44 46)
    # Some PDFs have a UTF-8 BOM or up to 1024 leading bytes, but standard is b"%PDF" in first 1024 bytes
    header_preview = file_bytes[:1024]
    if b"%PDF" not in header_preview:
        raise InvalidPDFException(filename, "File header does not match valid PDF magic bytes (%PDF)")


def validate_document(filename: str, file_bytes: bytes, max_mb: int = settings.MAX_FILE_SIZE_MB) -> None:
    """Validate an uploaded PDF or DOCX file before parsing it."""
    if not file_bytes:
        raise InvalidPDFException(filename, "Uploaded file is 0 bytes / empty")

    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > max_mb:
        raise FileTooLargeException(filename, size_mb, max_mb)

    extension = os.path.splitext(filename)[1].lower()
    if extension not in settings.ALLOWED_EXTENSIONS:
        raise InvalidPDFException(filename, "File extension must be .pdf or .docx")

    if extension == ".pdf":
        if b"%PDF" not in file_bytes[:1024]:
            raise InvalidPDFException(filename, "File header does not match valid PDF magic bytes (%PDF)")
        return

    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as archive:
            required_parts = {"[Content_Types].xml", "word/document.xml"}
            if not required_parts.issubset(archive.namelist()):
                raise InvalidPDFException(filename, "File is not a valid DOCX document")
    except (zipfile.BadZipFile, OSError) as exc:
        raise InvalidPDFException(filename, "File is not a valid DOCX document") from exc
