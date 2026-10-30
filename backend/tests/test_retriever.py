from app.rag import retriever


class FailingScoreSearch:
    def similarity_search_with_relevance_scores(self, query, k):
        raise RuntimeError("score search unavailable")


def test_retrieval_fails_closed_when_scored_search_fails(monkeypatch):
    monkeypatch.setattr(retriever, "get_total_chunks_count", lambda: 1)
    monkeypatch.setattr(retriever, "get_or_create_vectorstore", lambda: FailingScoreSearch())

    assert retriever.retrieve_relevant_chunks("example query") == []
