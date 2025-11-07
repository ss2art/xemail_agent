from langchain.prompts import PromptTemplate
import json

PROMPT = PromptTemplate.from_template(
    """Determine whether promotions or offers in the email are expired.
Say EXPIRED, ACTIVE, or UNKNOWN. Return JSON:
{"status": "<EXPIRED|ACTIVE|UNKNOWN>", "evidence": "<short reason>"}.
Email:
{email_text}
"""
)

def detect_expired(llm, email_text: str) -> dict:
    resp = llm.invoke(PROMPT.format(email_text=email_text))
    try:
        return json.loads(resp.content)
    except Exception:
        return {"status": "UNKNOWN", "evidence": resp.content.strip()[:200]}
