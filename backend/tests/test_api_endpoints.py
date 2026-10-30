from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from langchain_core.documents import Document

from app.core.config import settings
from app.models.chat import ChatResponse, SourceCitation
from app.services.chat_service import ChatService
from app.services import document_service
from app.rag import pipeline


def test_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "llm_provider" in data
    assert "embedding_provider" in data
    assert "total_chunks" in data


def test_documents_list_endpoint(client):
    res = client.get("/api/documents")
    assert res.status_code == 200
    data = res.json()
    assert "documents" in data
    assert "total_documents" in data
    assert "total_chunks" in data


def test_chat_empty_question(client):
    res = client.post("/api/chat", json={"question": "   ", "chat_history": []})
    assert res.status_code == 400
    data = res.json()
    assert data["error"] == "EmptyQuestionException"


def test_chat_response_includes_chunk_id(client, monkeypatch):
    expected = ChatResponse(
        answer="A cited answer.",
        sources=[
            SourceCitation(
                document="notes.pdf",
                page=2,
                chunk_index=7,
                content="Supporting text.",
                score=0.82,
            )
        ],
    )
    monkeypatch.setattr(
        ChatService,
        "answer_question",
        staticmethod(lambda request: expected),
    )

    response = client.post("/api/chat", json={"question": "What is cited?", "chat_history": []})

    assert response.status_code == 200
    assert response.json()["sources"][0]["chunk_index"] == 7


def test_chat_irrelevant_question_guardrail(client):
    res = client.post("/api/chat", json={"question": "What is the capital of Mars?", "chat_history": []})
    assert res.status_code == 200
    data = res.json()
    assert data["answer"] == "I couldn't find enough information in the uploaded documents to answer this question."
    assert data["sources"] == []


def test_chat_stream_emits_llm_error_event(client, monkeypatch):
    class FailingLLM:
        def stream(self, prompt):
            raise RuntimeError("model service unavailable")

    monkeypatch.setattr(
        pipeline,
        "retrieve_relevant_chunks",
        lambda **kwargs: [
            (
                Document(
                    page_content="A matching document chunk.",
                    metadata={"filename": "notes.pdf", "page": 1, "chunk_index": 0},
                ),
                0.6092,
            )
        ],
    )
    monkeypatch.setattr(pipeline, "get_llm", lambda **kwargs: FailingLLM())

    response = client.post(
        "/api/chat/stream",
        json={"question": "What does the document say?", "chat_history": []},
    )

    assert response.status_code == 200
    assert '"type": "error"' in response.text
    assert "LLM service unavailable:" in response.text


def test_upload_invalid_pdf(client):
    files = {"files": ("invalid.txt", b"plain text content", "application/pdf")}
    res = client.post("/api/documents/upload", files=files)
    assert res.status_code == 201
    data = res.json()
    assert data["success"] is False
    assert len(data["errors"]) > 0


def test_upload_pdf_and_docx(client, monkeypatch, tmp_path):
    seen_filenames = []

    def fake_load(file_path, filename):
        seen_filenames.append(filename)
        return [Document(page_content="A valid academic document for upload testing.", metadata={"page": 1})]

    monkeypatch.setattr(document_service, "load_and_preprocess_document", fake_load)
    monkeypatch.setattr(
        document_service,
        "split_documents",
        lambda **kwargs: [Document(page_content="A valid academic document for upload testing.", metadata={})],
    )
    monkeypatch.setattr(document_service, "add_documents_to_vectorstore", lambda chunks: len(chunks))
    monkeypatch.setattr(document_service, "find_document_by_hash", lambda file_hash: None)
    monkeypatch.setattr(document_service, "add_document_to_manifest", lambda meta: None)
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "MANIFEST_FILE", str(tmp_path / "uploads" / "manifest.json"))

    docx_buffer = BytesIO()
    with ZipFile(docx_buffer, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<document/>")

    files = [
        ("files", ("notes.pdf", b"%PDF-1.4 academic PDF fixture", "application/pdf")),
        (
            "files",
            (
                "notes.docx",
                docx_buffer.getvalue(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
        ),
    ]
    response = client.post("/api/documents/upload", files=files)

    assert response.status_code == 201
    result = response.json()
    assert result["success"] is True
    assert [item["filename"] for item in result["uploaded"]] == ["notes.pdf", "notes.docx"]
    assert seen_filenames == ["notes.pdf", "notes.docx"]
