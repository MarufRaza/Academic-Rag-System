import os
import shutil
import tempfile
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


@pytest.fixture(scope="session")
def client():
    """FastAPI TestClient fixture."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def isolated_env(tmp_path, monkeypatch):
    """
    Creates an isolated environment with temporary uploads and chroma_db directories.
    Ensures tests NEVER mutate or pollute the user's real Chroma database.
    """
    temp_upload = tmp_path / "uploads"
    temp_chroma = tmp_path / "chroma_db"
    temp_manifest = temp_upload / "documents_manifest.json"

    temp_upload.mkdir(parents=True, exist_ok=True)
    temp_chroma.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(settings, "UPLOAD_DIR", str(temp_upload))
    monkeypatch.setattr(settings, "CHROMA_PERSIST_DIR", str(temp_chroma))
    monkeypatch.setattr(settings, "MANIFEST_FILE", str(temp_manifest))
    monkeypatch.setattr(settings, "CHROMA_COLLECTION_NAME", "test_rag_collection")

    yield {
        "upload_dir": str(temp_upload),
        "chroma_dir": str(temp_chroma),
        "manifest": str(temp_manifest),
    }
