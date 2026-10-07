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


def test_chat_irrelevant_question_guardrail(client):
    res = client.post("/api/chat", json={"question": "What is the capital of Mars?", "chat_history": []})
    assert res.status_code == 200
    data = res.json()
    assert data["answer"] == "I couldn't find enough information in the uploaded documents to answer this question."
    assert data["sources"] == []


def test_upload_invalid_pdf(client):
    files = {"files": ("invalid.txt", b"plain text content", "application/pdf")}
    res = client.post("/api/documents/upload", files=files)
    assert res.status_code == 201
    data = res.json()
    assert data["success"] is False
    assert len(data["errors"]) > 0
