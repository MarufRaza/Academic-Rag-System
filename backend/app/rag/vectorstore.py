import os
import shutil
import threading
from typing import List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.core.config import settings
from app.core.exceptions import VectorStoreException, EmbeddingMismatchException
from app.core.logging import logger
from app.rag.embeddings import get_embedding_function, get_active_embedding_info

_chroma_client: Optional[chromadb.PersistentClient] = None
_vectorstore_instance: Optional[Chroma] = None
_vs_lock = threading.Lock()


def get_chroma_client() -> chromadb.PersistentClient:
    """Returns a singleton ChromaDB PersistentClient."""
    global _chroma_client
    if _chroma_client is None:
        os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
        try:
            _chroma_client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIR,
                settings=ChromaSettings(anonymized_telemetry=False)
            )
        except Exception as e:
            logger.error(f"Failed to initialize Chroma PersistentClient: {e}")
            raise VectorStoreException(f"Failed to connect to ChromaDB: {str(e)}")
    return _chroma_client


def get_or_create_vectorstore(force_reset: bool = False) -> Chroma:
    """
    Returns the singleton Chroma vectorstore.
    Verifies embedding provider/model signature stored in collection metadata.
    If there is a mismatch and not force_reset, raises EmbeddingMismatchException.
    """
    global _vectorstore_instance

    with _vs_lock:
        if _vectorstore_instance is not None and not force_reset:
            return _vectorstore_instance

        client = get_chroma_client()
        active_info = get_active_embedding_info()
        current_sig = active_info["signature"]
        embedding_func = get_embedding_function()

        collection_name = settings.CHROMA_COLLECTION_NAME

        try:
            # Check existing collections
            existing_colls = [c.name for c in client.list_collections()]
            if collection_name in existing_colls:
                existing_coll = client.get_collection(collection_name)
                coll_meta = existing_coll.metadata or {}
                saved_sig = coll_meta.get("embedding_signature")

                if saved_sig and saved_sig != current_sig:
                    if force_reset:
                        logger.warning(
                            f"Resetting collection '{collection_name}' due to embedding mismatch: "
                            f"{saved_sig} -> {current_sig}"
                        )
                        client.delete_collection(collection_name)
                    else:
                        raise EmbeddingMismatchException(
                            current_info=current_sig,
                            saved_info=saved_sig
                        )

            # Create or get collection with cosine distance and embedding signature
            vectorstore = Chroma(
                client=client,
                collection_name=collection_name,
                embedding_function=embedding_func,
                collection_metadata={
                    "hnsw:space": "cosine",
                    "embedding_signature": current_sig,
                    "embedding_provider": active_info["provider"],
                    "embedding_model": active_info["model"]
                }
            )

            _vectorstore_instance = vectorstore
            logger.info(f"Connected to Chroma collection '{collection_name}' with signature: {current_sig}")
            return _vectorstore_instance

        except EmbeddingMismatchException:
            raise
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise VectorStoreException(str(e))


def add_documents_to_vectorstore(documents: List[Document]) -> int:
    """Adds split chunks to the vectorstore and returns the count."""
    if not documents:
        return 0

    try:
        vectorstore = get_or_create_vectorstore()
        vectorstore.add_documents(documents)
        logger.info(f"Successfully embedded and indexed {len(documents)} chunks into ChromaDB.")
        return len(documents)
    except Exception as e:
        logger.error(f"Failed to add documents to ChromaDB: {e}")
        raise VectorStoreException(f"Failed to embed and index chunks: {str(e)}")


def delete_documents_by_id(document_id: str) -> int:
    """
    Deletes all vector chunks associated with the specified document_id.
    Returns the number of deleted chunks.
    """
    try:
        client = get_chroma_client()
        existing_colls = [c.name for c in client.list_collections()]
        if settings.CHROMA_COLLECTION_NAME not in existing_colls:
            return 0

        collection = client.get_collection(settings.CHROMA_COLLECTION_NAME)
        # Find matching IDs first to report accurate count
        results = collection.get(where={"document_id": document_id})
        ids_to_delete = results.get("ids", [])
        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
            logger.info(f"Deleted {len(ids_to_delete)} chunks for document_id '{document_id}'.")
            return len(ids_to_delete)
        return 0
    except Exception as e:
        logger.error(f"Failed to delete chunks for document_id '{document_id}': {e}")
        raise VectorStoreException(f"Failed to remove document chunks from vector store: {str(e)}")


def get_total_chunks_count() -> int:
    """Returns the total number of items in the Chroma collection."""
    try:
        client = get_chroma_client()
        existing_colls = [c.name for c in client.list_collections()]
        if settings.CHROMA_COLLECTION_NAME not in existing_colls:
            return 0
        coll = client.get_collection(settings.CHROMA_COLLECTION_NAME)
        return coll.count()
    except Exception as e:
        logger.warning(f"Error fetching chunk count: {e}")
        return 0


def reset_vectorstore() -> None:
    """Completely resets the ChromaDB collection and cached instance."""
    global _vectorstore_instance, _chroma_client
    with _vs_lock:
        try:
            client = get_chroma_client()
            existing_colls = [c.name for c in client.list_collections()]
            if settings.CHROMA_COLLECTION_NAME in existing_colls:
                client.delete_collection(settings.CHROMA_COLLECTION_NAME)
            _vectorstore_instance = None
            logger.info("Chroma vectorstore collection reset.")
        except Exception as e:
            logger.error(f"Failed to reset vectorstore collection: {e}")
            raise VectorStoreException(str(e))
