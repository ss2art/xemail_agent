# Smoke test for the full agent pipeline without external services.
# Uses fake LLM and vectorstore to avoid network calls.

import os
import sys
from typing import Any

# Ensure package imports work when running from repo root
CURR = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(CURR, ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from agents.controller_agent import process_batch  # type: ignore


class _Resp:
    """Simple response wrapper mirroring langchain message content."""

    def __init__(self, content: str):
        """Store the response content used by the stubbed LLM."""
        self.content = content


class FakeLLM:
    """Minimal LLM stub that returns deterministic responses for prompts."""

    def invoke(self, prompt_or_messages: Any, **kwargs):
        """Return a canned response based on the prompt text."""
        text = str(prompt_or_messages)
        if "expert email triage assistant" in text:
            # classification prompt
            return _Resp("Marketing")
        if "Determine whether promotions or offers in the email are expired" in text:
            # temporal prompt
            return _Resp('{"status": "ACTIVE", "evidence": "stub"}')
        if "Identify if this email relates to a recurring subscription" in text:
            # subscription prompt
            return _Resp('{"is_subscription": true, "vendor": "Acme", "has_unsubscribe": true}')
        # Default fallback
        return _Resp("Other")


class FakeVectorStore:
    """Vector store stub that records added docs and returns empty searches."""

    def __init__(self):
        """Initialize an in-memory doc list."""
        self._docs = []

    def add_documents(self, docs):
        """Record documents for inspection."""
        self._docs.extend(docs)

    def similarity_search(self, query: str, k: int = 5):
        """Return an empty list to avoid external dependency lookups."""
        return []


def run() -> int:
    """
    Execute the smoke flow: process two emails and assert enrichment outcomes.

    Returns:
        Exit code 0 on success.
    """
    os.environ.setdefault("ENABLE_GUARDRAIL", "True")

    items = [
        {
            "subject": "Weekly Deals",
            "from": "news@acme.com",
            "raw": "<html><body><h1>Big Sale</h1><p>Save 50% this week</p></body></html>",
            "date": "2024-10-10",
        },
        {
            # This one should be REJECTED by guardrail (empty body)
            "subject": "",
            "from": "",
            "raw": "",
            "date": "2024-10-11",
        },
    ]

    llm = FakeLLM()
    vs = FakeVectorStore()

    results = process_batch(llm, vs, items)

    assert len(results) == 2, f"Expected 2 results, got {len(results)}"

    r0 = results[0]
    assert r0.get("category") == "Marketing", f"Unexpected category: {r0.get('category')}"
    assert r0.get("guardrail", {}).get("status") in ("OK", "WARN"), f"Guardrail status unexpected: {r0.get('guardrail')}"
    assert r0.get("temporal", {}).get("status") == "ACTIVE", f"Temporal status unexpected: {r0.get('temporal')}"
    assert r0.get("subscription", {}).get("is_subscription") is True, f"Subscription parse unexpected: {r0.get('subscription')}"

    r1 = results[1]
    assert r1.get("category") == "Rejected", f"Second item should be Rejected, got: {r1.get('category')}"
    assert r1.get("guardrail", {}).get("status") == "REJECTED", f"Second item guardrail not REJECTED: {r1.get('guardrail')}"

    print("Smoke test passed: full agent pipeline OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())


def test_full_agent_smoke():
    """Ensure the smoke runner completes without raising assertions."""
    assert run() == 0
