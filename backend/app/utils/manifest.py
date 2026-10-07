import json
import os
import threading
from typing import Dict, List, Optional
from app.core.config import settings
from app.core.logging import logger
from app.models.document import DocumentMetadata

_manifest_lock = threading.Lock()


def _ensure_manifest_file() -> None:
    os.makedirs(os.path.dirname(settings.MANIFEST_FILE), exist_ok=True)
    if not os.path.exists(settings.MANIFEST_FILE):
        with open(settings.MANIFEST_FILE, "w", encoding="utf-8") as f:
            json.dump({"documents": {}}, f, indent=2)


def get_manifest() -> Dict[str, dict]:
    _ensure_manifest_file()
    with _manifest_lock:
        try:
            with open(settings.MANIFEST_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("documents", {})
        except Exception as e:
            logger.error(f"Error reading manifest: {e}")
            return {}


def save_manifest(documents: Dict[str, dict]) -> None:
    _ensure_manifest_file()
    with _manifest_lock:
        temp_file = f"{settings.MANIFEST_FILE}.tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump({"documents": documents}, f, indent=2)
        os.replace(temp_file, settings.MANIFEST_FILE)


def add_document_to_manifest(meta: DocumentMetadata) -> None:
    docs = get_manifest()
    docs[meta.document_id] = meta.model_dump()
    save_manifest(docs)


def get_document_by_id(document_id: str) -> Optional[DocumentMetadata]:
    docs = get_manifest()
    doc_dict = docs.get(document_id)
    if doc_dict:
        return DocumentMetadata(**doc_dict)
    return None


def find_document_by_hash(file_hash: str) -> Optional[DocumentMetadata]:
    docs = get_manifest()
    for doc_dict in docs.values():
        if doc_dict.get("file_hash") == file_hash:
            return DocumentMetadata(**doc_dict)
    return None


def remove_document_from_manifest(document_id: str) -> Optional[DocumentMetadata]:
    docs = get_manifest()
    if document_id in docs:
        removed = docs.pop(document_id)
        save_manifest(docs)
        return DocumentMetadata(**removed)
    return None


def list_all_documents() -> List[DocumentMetadata]:
    docs = get_manifest()
    results = []
    for doc_dict in docs.values():
        try:
            results.append(DocumentMetadata(**doc_dict))
        except Exception as e:
            logger.warning(f"Error parsing document metadata: {e}")
    # Sort newest first
    results.sort(key=lambda d: d.upload_date, reverse=True)
    return results
