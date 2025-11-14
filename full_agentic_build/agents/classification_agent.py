from langchain_core.prompts import PromptTemplate

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
    try:
        resp = llm.invoke(PROMPT.format(email_text=email_text))
    except Exception:
        resp = llm.invoke(PROMPT.format(email_text=email_text[:12000]))
    text = getattr(resp, "content", str(resp)).strip()
    return text.splitlines()[0].strip()
