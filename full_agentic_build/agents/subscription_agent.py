from langchain.prompts import PromptTemplate
import json

PROMPT = PromptTemplate.from_template(
    """Identify if this email relates to a recurring subscription or newsletter.
Return JSON: {"is_subscription": true/false, "vendor": "<name or null>", "has_unsubscribe": true/false}.
Email:
{email_text}
"""
)

def detect_subscription(llm, email_text: str) -> dict:
    resp = llm.invoke(PROMPT.format(email_text=email_text))
    try:
        return json.loads(resp.content)
    except Exception:
        return {"is_subscription": False, "vendor": None, "has_unsubscribe": False}
