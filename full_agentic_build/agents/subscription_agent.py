"""Detect subscription/newsletter patterns in email text."""

import json

from langchain_core.prompts import PromptTemplate
from agents.utils import invoke_with_retry, parse_json_response

PROMPT = PromptTemplate.from_template(
    """Identify if this email relates to a recurring subscription or newsletter.
Return JSON: {{"is_subscription": true/false, "vendor": "<name or null>", "has_unsubscribe": true/false}}.

Email:
{email_text}
"""
)

def detect_subscription(llm, email_text: str) -> dict:
    """
    Determine whether an email is a subscription/newsletter.

    Args:
        llm: LLM adapter used to evaluate the prompt.
        email_text: Email body text.

    Returns:
        Dict containing is_subscription/vendor/has_unsubscribe flags.
    """
    resp = invoke_with_retry(llm, PROMPT.format(email_text=email_text[:12000]))
    return parse_json_response(
        resp,
        {"is_subscription": False, "vendor": None, "has_unsubscribe": False},
    )
