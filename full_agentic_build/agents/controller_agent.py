import os
from typing import List, Dict
from .guardrail_agent import validate_email
from .classification_agent import classify_email
from .temporal_agent import detect_expired
from .subscription_agent import detect_subscription
from .semantic_agent import index_documents

ENABLE_GUARDRAIL = os.getenv("ENABLE_GUARDRAIL", "True").lower() == "true"

def process_batch(llm, vectorstore, items: List[Dict]) -> List[Dict]:
    results = []
    docs_for_index = []
    for it in items:
        guard = {"status": "SKIPPED", "notes": []}
        if ENABLE_GUARDRAIL:
            guard = validate_email(it)
            if guard["status"] == "REJECTED":
                it["category"] = "Rejected"
                it["guardrail"] = guard
                results.append(it)
                continue

        text = it.get("text", "")
        category = classify_email(llm, text)
        temporal = detect_expired(llm, text)
        subs = detect_subscription(llm, text)

        enriched = {**it, "category": category, "temporal": temporal, "subscription": subs, "guardrail": guard}
        results.append(enriched)
        docs_for_index.append({"content": text, "meta": {"category": category, "path": it.get("path", "")}})

    if docs_for_index:
        index_documents(vectorstore, docs_for_index)
    return results
