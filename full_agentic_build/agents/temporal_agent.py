"""Detect whether an offer/promotion is expired, active, or unknown."""

import json

from langchain_core.prompts import PromptTemplate
from agents.utils import invoke_with_retry, parse_json_response

PROMPT = PromptTemplate.from_template(
    """Determine whether promotions or offers in the email are expired.
Say EXPIRED, ACTIVE, or UNKNOWN. Return JSON:
{{"status": "<EXPIRED|ACTIVE|UNKNOWN>", "evidence": "<short reason>"}}.

Email:
{email_text}
"""
)

def detect_expired(llm, email_text: str) -> dict:
    """
    Classify the temporal status of promotions in an email.

    Args:
        llm: LLM adapter used to evaluate the prompt.
        email_text: Email body text.

    Returns:
        Dict with status and evidence string.
    """
    resp = invoke_with_retry(llm, PROMPT.format(email_text=email_text[:12000]))
    return parse_json_response(
        resp,
        {"status": "UNKNOWN", "evidence": "Parsing failed"},
    )
