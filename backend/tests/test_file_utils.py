import pytest
from app.utils.file_utils import (
    validate_pdf,
    compute_file_hash,
    format_file_size,
    sanitize_filename,
)
from app.core.exceptions import InvalidPDFException, FileTooLargeException


def test_compute_file_hash():
    data = b"Academic RAG Test Content"
    hash1 = compute_file_hash(data)
    hash2 = compute_file_hash(data)
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 length


def test_format_file_size():
    assert format_file_size(500) == "500 B"
    assert format_file_size(2048) == "2.0 KB"
    assert format_file_size(5 * 1024 * 1024) == "5.00 MB"


def test_sanitize_filename():
    assert sanitize_filename("../../../etc/passwd.pdf") == "passwd.pdf"
    assert sanitize_filename("lecture 01 notes!.pdf") == "lecture 01 notes_.pdf"


def test_validate_pdf_valid():
    valid_pdf_bytes = b"%PDF-1.4 sample pdf content for test"
    # Should not raise exception
    validate_pdf("sample.pdf", valid_pdf_bytes, max_mb=25)


def test_validate_pdf_invalid_magic_bytes():
    fake_pdf = b"NOT_A_PDF_CONTENT"
    with pytest.raises(InvalidPDFException) as exc:
        validate_pdf("sample.pdf", fake_pdf, max_mb=25)
    assert "magic bytes" in str(exc.value.detail).lower()


def test_validate_pdf_empty():
    with pytest.raises(InvalidPDFException) as exc:
        validate_pdf("empty.pdf", b"", max_mb=25)
    assert "empty" in str(exc.value.detail).lower()


def test_validate_pdf_too_large():
    huge_bytes = b"%PDF-" + b"0" * (1024 * 1024 + 100)
    with pytest.raises(FileTooLargeException):
        validate_pdf("huge.pdf", huge_bytes, max_mb=1)
