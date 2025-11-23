"""
Batch controller to run guardrail, classification, and indexing steps.
"""

import os
from typing import List, Dict

from .classification_agent import classify_email
from .guardrail_agent import validate_email
from .parsing_agent import extract_text
from .semantic_agent import index_documents
from .subscription_agent import detect_subscription
from .temporal_agent import detect_expired
from services.storage_service import ensure_uid

ENABLE_GUARDRAIL = os.getenv("ENABLE_GUARDRAIL", "True").lower() == "true"

def process_batch(llm, vectorstore, items: List[Dict]) -> List[Dict]:
    """
    Process a batch of email dicts through guardrail, classification, temporal/subscription
    detection, and vector indexing.

    Args:
        llm: LLM adapter used for classification and detectors.
        vectorstore: Vector store to receive embeddings.
        items: List of email-like dicts to enrich.

    Returns:
        List of enriched email dicts with categories, guardrail, temporal, and subscription data.
    """
    results = []
    docs_for_index = []
    for it in items:
        uid = ensure_uid(it)
        guard = {"status": "SKIPPED", "notes": []}
        if ENABLE_GUARDRAIL:
            guard = validate_email(it)
            if guard["status"] == "REJECTED":
                categories = list(dict.fromkeys((it.get("categories") or []) + ["Rejected"]))
                it.update({"guardrail": guard, "category": "Rejected", "categories": categories, "temporal": {}, "subscription": {}})
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
        categories = list(dict.fromkeys((it.get("categories") or []) + ([category] if category else [])))
        enriched = {**it, "uid": uid, "text": text, "category": category, "categories": categories, "temporal": temporal, "subscription": subscription, "guardrail": guard}
        results.append(enriched)
        if text:
            meta_categories = ", ".join(categories) if categories else None
            meta = {
                "subject": it.get("subject",""),
                "from": it.get("from") or it.get("from_addr",""),
                "category": category,
                "categories": meta_categories,
                "date": it.get("date",""),
                "id": uid,
                "uid": uid,
                "folder": it.get("folder"),
                "message_id": it.get("message_id"),
            }
            docs_for_index.append({"content": text, "meta": meta})
    try:
        index_documents(vectorstore, docs_for_index)
    except Exception as e:
        print("Indexing error:", e)
    return results
