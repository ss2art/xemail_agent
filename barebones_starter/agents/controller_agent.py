import os
from typing import List, Dict
from .guardrail_agent import validate_email
from .classification_agent import classify_email

ENABLE_GUARDRAIL = os.getenv("ENABLE_GUARDRAIL", "True").lower() == "true"

def process_batch(llm, items: List[Dict]) -> List[Dict]:
    results = []
    for it in items:
        guard = {"status": "SKIPPED", "notes": []}
        if ENABLE_GUARDRAIL:
            guard = validate_email(it)
            if guard["status"] == "REJECTED":
                it["category"] = "Rejected"
                it["guardrail"] = guard
                results.append(it)
                continue

        text = it.get("text", it.get("raw",""))
        category = classify_email(llm, text)
        it["category"] = category
        it["guardrail"] = guard
        results.append(it)
    return results
