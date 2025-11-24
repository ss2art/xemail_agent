"""Detect subscription/newsletter patterns in email text."""

import json

from langchain_core.prompts import PromptTemplate

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
    resp = llm.invoke(PROMPT.format(email_text=email_text[:12000]))
    try:
        return json.loads(getattr(resp, "content", str(resp)))
    except Exception:
        return {"is_subscription": False, "vendor": None, "has_unsubscribe": False}
