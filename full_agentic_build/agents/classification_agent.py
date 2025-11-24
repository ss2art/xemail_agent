"""LLM-based single-label email classification."""

from langchain_core.prompts import PromptTemplate
from agents.utils import invoke_with_retry

PROMPT = PromptTemplate.from_template(
    """You are an expert email triage assistant.
Categorize the email into ONE of the following high-level classes:
[Job, Marketing, Subscription, Personal, Finance, Newsletter, Receipt/Bill, Phishing, Other]

Return only the single class label.

Email:
{email_text}
"""
)

def classify_email(llm, email_text: str) -> str:
    """
    Classify an email into one of the predefined categories.

    Args:
        llm: LLM adapter used to run the prompt.
        email_text: Email body text.

    Returns:
        Chosen category label string.
    """
    def _call(prompt_text: str):
        return invoke_with_retry(llm, PROMPT.format(email_text=prompt_text))

    try:
        resp = _call(email_text)
    except Exception:
        resp = _call(email_text[:12000])
    text = getattr(resp, "content", str(resp)).strip()
    return text.splitlines()[0].strip()
