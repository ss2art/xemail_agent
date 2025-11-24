import os
import sys

# Ensure package imports work when running from repo root
CURR = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(CURR, ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from agents.classification_agent import classify_email  # type: ignore
from agents.subscription_agent import detect_subscription  # type: ignore
from agents.temporal_agent import detect_expired  # type: ignore
from agents.guardrail_agent import validate_email  # type: ignore


class _Resp:
    def __init__(self, content: str):
        self.content = content


class _LLM:
    def __init__(self, responses):
        self.calls = []
        self.responses = responses

    def invoke(self, prompt):
        self.calls.append(prompt)
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return _Resp(item)


def test_classify_email_returns_first_line():
    llm = _LLM(["Marketing\nExtra"])
    result = classify_email(llm, "Sample body text")
    assert result == "Marketing"
    assert len(llm.calls) == 1


def test_detect_subscription_parses_json_response():
    llm = _LLM(['{"is_subscription": true, "vendor": "Acme", "has_unsubscribe": true}'])
    result = detect_subscription(llm, "Newsletter body")
    assert result["is_subscription"] is True
    assert result["vendor"] == "Acme"
    assert result["has_unsubscribe"] is True


def test_detect_subscription_falls_back_on_bad_json():
    llm = _LLM(["not-json"])
    result = detect_subscription(llm, "Bad body")
    assert result["is_subscription"] is False
    assert result["vendor"] is None
    assert result["has_unsubscribe"] is False


def test_detect_expired_returns_status_and_evidence():
    llm = _LLM(['{"status": "EXPIRED", "evidence": "offer ended"}'])
    result = detect_expired(llm, "Promo body")
    assert result["status"] == "EXPIRED"
    assert "offer ended" in result.get("evidence", "")


def test_validate_email_guardrails_missing_fields():
    result = validate_email({"raw": "", "subject": "", "from": ""})
    assert result["status"] == "REJECTED"
    assert "Empty email body." in result["notes"]
