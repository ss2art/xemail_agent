import os
import sys
from typing import List, Tuple

from langchain_core.documents import Document

# Ensure package imports work when running from repo root
CURR = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(CURR, ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services import search_service  # type: ignore
from services.search_service import search_emails, validate_category_name  # type: ignore


class _FakeVectorWithScores:
    def __init__(self, docs_with_scores: List[Tuple[Document, float]]):
        self.docs_with_scores = docs_with_scores

    def similarity_search_with_score(self, query: str, k: int = 5):
        return self.docs_with_scores[:k]


class _FakeVectorNoScores:
    def __init__(self, docs: List[Document]):
        self.docs = docs

    def similarity_search_with_score(self, query: str, k: int = 5):
        raise AttributeError("no similarity_search_with_score")

    def similarity_search(self, query: str, k: int = 5):
        return self.docs[:k]


def test_search_emails_normalizes_results_and_applies_category(monkeypatch):
    """
    Ensure the search service returns normalized result dicts and persists
    applied category labels to the corpus. Validates:
    - Limits are respected via env defaults
    - Categories from corpus metadata are preserved
    - Applied category propagates to results and is sent to apply_category_label
    - Scores from similarity_search_with_score are retained
    """
    monkeypatch.setenv("SEARCH_MAX_LIMIT", "5")
    monkeypatch.setenv("SEARCH_DEFAULT_LIMIT", "3")
    # Provide in-memory corpus to avoid file writes
    fake_corpus = [
        {"uid": "1", "subject": "Alpha", "categories": ["Existing"]},
        {"uid": "2", "subject": "Beta", "categories": []},
    ]
    monkeypatch.setattr(search_service, "load_corpus", lambda: fake_corpus)
    applied_ids = []
    monkeypatch.setattr(search_service, "apply_category_label", lambda ids, category: applied_ids.extend(ids) or True)

    print("\n Test: normalize results, apply category, preserve scores and categories")
    docs = [
        (Document(page_content="Alpha body text", metadata={"uid": "1", "subject": "Alpha", "from": "a@test", "date": "2024-01-01", "category": "Marketing"}), 0.1),
        (Document(page_content="Beta body text", metadata={"uid": "2", "subject": "Beta", "from": "b@test", "date": "2024-01-02", "category": "Job"}), 0.2),
        (Document(page_content="Gamma body text", metadata={"uid": "3", "subject": "Gamma", "from": "c@test", "date": "2024-01-03", "category": "Other"}), 0.3),
    ]
    vector = _FakeVectorWithScores(docs)

    results = search_emails(vector, query="body", limit=3, category_name="Leads")

    assert len(results) == 3
    assert all(r["applied_category"] == "Leads" for r in results)
    assert "Leads" in results[0]["categories"]
    assert results[0]["id"] == "1"
    assert results[0]["score"] == 0.1
    assert "Alpha" in results[0]["subject"]
    assert results[1]["sender"] == "b@test"
    assert applied_ids == ["1", "2", "3"]


def test_search_emails_clamps_limit_and_falls_back_without_scores(monkeypatch):
    """
    Verify limit clamping and fallback when similarity_search_with_score is
    unavailable. Validates:
    - limit > max is clamped to SEARCH_MAX_LIMIT
    - score is None when using similarity_search fallback
    - snippets are generated and ids are preserved
    """
    monkeypatch.setenv("SEARCH_MAX_LIMIT", "2")
    monkeypatch.setenv("SEARCH_DEFAULT_LIMIT", "1")
    monkeypatch.setattr(search_service, "load_corpus", lambda: [])
    monkeypatch.setattr(search_service, "apply_category_label", lambda ids, category: True)
    print("Test: clamp limit and fallback path when scores are unavailable")
    docs = [
        Document(page_content="First doc content", metadata={"uid": "a"}),
        Document(page_content="Second doc content", metadata={"uid": "b"}),
        Document(page_content="Third doc content", metadata={"uid": "c"}),
    ]
    vector = _FakeVectorNoScores(docs)

    results = search_emails(vector, query="doc", limit=10, category_name=None)

    assert len(results) == 2  # clamped by SEARCH_MAX_LIMIT
    assert results[0]["score"] is None  # fallback path
    assert results[0]["snippet"].startswith("First doc content")
    assert results[1]["id"] == "b"


def test_search_emails_filters_by_category(monkeypatch):
    """
    Ensure filter_category limits returned results to matching categories (case-insensitive).
    """
    monkeypatch.setenv("SEARCH_MAX_LIMIT", "5")
    monkeypatch.setenv("SEARCH_DEFAULT_LIMIT", "5")
    monkeypatch.setattr(search_service, "load_corpus", lambda: [])
    monkeypatch.setattr(search_service, "apply_category_label", lambda ids, category: True)
    print("Test: filter results by category (case-insensitive)")
    docs = [
        (Document(page_content="Doc one", metadata={"uid": "1", "categories": ["Finance"]}), 0.1),
        (Document(page_content="Doc two", metadata={"uid": "2", "categories": ["finance", "job"]}), 0.2),
        (Document(page_content="Doc three", metadata={"uid": "3", "categories": ["Marketing"]}), 0.3),
    ]
    vector = _FakeVectorWithScores(docs)

    results = search_emails(vector, query="doc", filter_category="FINANCE")

    assert len(results) == 2
    assert {r["id"] for r in results} == {"1", "2"}


def test_validate_category_name_enforces_rules():
    """
    Validate category name guardrails (non-empty, length, allowed chars).
    """
    print("Test: validate category name rules and failure cases")
    assert validate_category_name("Finance-2025") == "Finance-2025"
    assert validate_category_name(None) is None
    for bad in ["", "   ", "x" * 65, "name!"]:
        try:
            validate_category_name(bad)
            assert False, f"Expected validation failure for: {bad!r}"
        except ValueError:
            pass


def test_search_emails_rejects_invalid_category(monkeypatch):
    """
    search_emails should raise for invalid category/tag inputs.
    """
    print("Test: search_emails rejects invalid category names")
    monkeypatch.setattr(search_service, "load_corpus", lambda: [])
    vector = _FakeVectorNoScores([])
    try:
        search_emails(vector, query="q", category_name="bad!name")
        assert False, "Expected ValueError for invalid category_name"
    except ValueError:
        pass
