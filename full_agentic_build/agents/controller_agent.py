import os
from typing import List, Dict
from .guardrail_agent import validate_email
from .classification_agent import classify_email
from .temporal_agent import detect_expired
from .subscription_agent import detect_subscription
from .parsing_agent import extract_text
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
                it.update({"guardrail": guard, "category": "Rejected", "temporal": {}, "subscription": {}})
                results.append(it)
                continue
        # Prefer markdown/text fields from EmailRecord; fallback to extracted raw
        text = (
            it.get("body_markdown")
            or it.get("text")
            or it.get("body_text")
            or extract_text(it.get("body_raw") or it.get("raw", ""))
        )
        category = classify_email(llm, text) if text else "Other"
        temporal = detect_expired(llm, text) if text else {"status":"UNKNOWN","evidence":"no text"}
        subscription = detect_subscription(llm, text) if text else {"is_subscription":False,"vendor":None,"has_unsubscribe":False}
        enriched = {**it, "text": text, "category": category, "temporal": temporal, "subscription": subscription, "guardrail": guard}
        results.append(enriched)
        if text:
            meta = {
                "subject": it.get("subject",""),
                "from": it.get("from") or it.get("from_addr",""),
                "category": category,
                "uid": it.get("uid"),
                "folder": it.get("folder"),
                "message_id": it.get("message_id"),
            }
            docs_for_index.append({"content": text, "meta": meta})
    try:
        index_documents(vectorstore, docs_for_index)
    except Exception as e:
        print("Indexing error:", e)
    return results
