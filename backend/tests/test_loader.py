from pathlib import Path

from langchain_core.documents import Document

from app.rag import loader
from app.rag.splitter import split_documents


def test_load_and_preprocess_document_routes_by_extension(monkeypatch):
    pdf_result = [object()]
    docx_result = [object()]
    monkeypatch.setattr(loader, "load_and_preprocess_pdf", lambda path, name: pdf_result)
    monkeypatch.setattr(loader, "load_and_preprocess_docx", lambda path, name: docx_result)

    assert loader.load_and_preprocess_document("notes.pdf", "notes.pdf") is pdf_result
    assert loader.load_and_preprocess_document("notes.docx", "notes.docx") is docx_result


def test_docx_loader_preserves_uploaded_source_metadata(monkeypatch, tmp_path):
    class FakeDocx2txtLoader:
        def __init__(self, file_path):
            self.file_path = file_path

        def load(self):
            return [Document(
                page_content="A meaningful searchable Word document body.",
                metadata={"source": self.file_path},
            )]

    import langchain_community.document_loaders

    monkeypatch.setattr(
        langchain_community.document_loaders,
        "Docx2txtLoader",
        FakeDocx2txtLoader,
        raising=False,
    )
    docx_path = tmp_path / "source.docx"
    docx_path.write_bytes(b"test")

    result = loader.load_and_preprocess_docx(str(docx_path), "source.docx")

    assert result[0].metadata["source"] == "source.docx"
    assert result[0].metadata["filename"] == "source.docx"
    assert result[0].metadata["page"] == 1


def test_real_sample_docx_loads_and_splits_with_source_metadata():
    sample_path = (
        Path(__file__).resolve().parents[1]
        / "sample_documents"
        / "RAG_Docx_Sample.docx"
    )

    documents = loader.load_and_preprocess_document(
        str(sample_path),
        sample_path.name,
    )
    chunks = split_documents(
        documents=documents,
        document_id="real-docx-test",
        filename=sample_path.name,
        file_hash="real-docx-test-hash",
        chunk_size=180,
        chunk_overlap=20,
    )

    assert documents
    assert "retrieval augmented generation" in documents[0].page_content.lower()
    assert len(chunks) > 1
    assert all(chunk.metadata["filename"] == sample_path.name for chunk in chunks)
    assert all(chunk.metadata["page"] == 1 for chunk in chunks)
    assert [chunk.metadata["chunk_index"] for chunk in chunks] == list(range(len(chunks)))
