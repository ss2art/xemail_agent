import os
import re
from typing import Any, Dict, List, Optional, Tuple

from langchain_core.documents import Document

from services.storage_service import apply_category_label, ensure_uid, load_corpus


def _limit_bounds() -> Tuple[int, int]:
    """Return (default_limit, max_limit) parsed from environment with sane floors."""
    try:
        default_limit = int(os.getenv("SEARCH_DEFAULT_LIMIT", "8"))
    except Exception:
        default_limit = 8
    try:
        max_limit = int(os.getenv("SEARCH_MAX_LIMIT", "50"))
    except Exception:
        max_limit = 50
    # Ensure defaults are at least 1 and not above max
    default_limit = max(1, min(default_limit, max_limit))
    max_limit = max(1, max_limit)
    return default_limit, max_limit


def _normalize_limit(limit: Optional[int]) -> int:
    """Clamp requested limit to configured bounds."""
    default_limit, max_limit = _limit_bounds()
    if limit is None:
        return default_limit
    try:
        value = int(limit)
    except Exception:
        return default_limit
    if value <= 0:
        return default_limit
    return min(value, max_limit)


def _search_with_scores(vectorstore, query: str, k: int):
    """
    Attempt similarity_search_with_score with safe fallback to similarity_search.

    Args:
        vectorstore: Vector store client supporting similarity search.
        query: Query text.
        k: Number of hits to request.

    Returns:
        List of (Document, score) tuples; score is None on fallback.
    """
    try:
        return vectorstore.similarity_search_with_score(query, k=k)
    except Exception:
        try:
            docs = vectorstore.similarity_search(query, k=k)
            return [(doc, None) for doc in docs]
        except Exception:
            return []


def _snippet(text: str, length: int = 200) -> str:
    """Collapse whitespace and trim to a fixed preview length."""
    if not text:
        return ""
    clean = " ".join(text.split())
    return clean if len(clean) <= length else f"{clean[:length].rstrip()}..."


_CATEGORY_RE = re.compile(r"^[\w\s\-_/]{1,64}$")


def validate_category_name(name: Optional[str]) -> Optional[str]:
    """
    Ensure category names are non-empty, bounded in length, and avoid odd chars.
    Returns stripped name or raises ValueError for invalid inputs.
    """
    if name is None:
        return None
    stripped = name.strip()
    if not stripped:
        raise ValueError("Category name cannot be empty.")
    if len(stripped) > 64:
        raise ValueError("Category name too long (max 64 characters).")
    if not _CATEGORY_RE.match(stripped):
        raise ValueError("Category name contains invalid characters.")
    return stripped


def get_limit_defaults() -> Tuple[int, int]:
    """Expose (default_limit, max_limit) for UI controls and callers."""
    return _limit_bounds()


def search_emails(
    vectorstore,
    query: str,
    limit: Optional[int] = None,
    category_name: Optional[str] = None,
    filter_category: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Unified search API for emails with limit validation and optional category tagging.

    Returns a normalized list of dictionaries with id, subject, sender, date, snippet,
    score (if available), existing category, and the applied category label.
    """
    if not query:
        return []

    category_name = validate_category_name(category_name)
    filter_category = validate_category_name(filter_category)

    k = _normalize_limit(limit)
    raw_hits = _search_with_scores(vectorstore, query, k=k)

    # Map stored corpus by id for enriched categories and persistence.
    corpus = load_corpus()
    corpus_by_id = {}
    for item in corpus:
        identifier = item.get("uid") or item.get("message_id")
        if identifier:
            corpus_by_id[identifier] = item

    results: List[Dict[str, Any]] = []
    def _category_list(value: Any) -> List[str]:
        """Normalize categories field to a list of strings."""
        if value is None:
            return []
        if isinstance(value, str):
            value = value.strip()
            return [value] if value else []
        if isinstance(value, list):
            # Filter to simple scalars
            out = []
            for v in value:
                if isinstance(v, str):
                    if v.strip():
                        out.append(v.strip())
                elif isinstance(v, (int, float, bool)):
                    out.append(str(v))
            return out
        return []

    for doc, score in raw_hits[:k]:
        metadata = getattr(doc, "metadata", {}) or {}
        content = getattr(doc, "page_content", "") or ""
        uid = metadata.get("uid") or metadata.get("message_id") or metadata.get("id")
        if not uid:
            uid = ensure_uid(metadata)
        corpus_categories = _category_list(corpus_by_id.get(uid, {}).get("categories"))
        categories = corpus_categories or _category_list(metadata.get("categories"))
        if category_name and category_name not in categories:
            categories = [*categories, category_name]
        results.append(
            {
                "id": uid,
                "subject": metadata.get("subject", ""),
                "sender": metadata.get("from", "") or metadata.get("from_addr", ""),
                "date": metadata.get("date", ""),
                "category": metadata.get("category"),
                "categories": categories,
                "applied_category": category_name or None,
                "snippet": _snippet(content),
                "score": score,
                "metadata": metadata,
            }
        )

    # Optional category filter (case-insensitive match)
    if filter_category:
        fc_lower = filter_category.lower()
        results = [
            r for r in results
            if any((c or "").lower() == fc_lower for c in (r.get("categories") or []))
        ]

    # Persist the applied category for future searches if provided.
    if category_name:
        ids = [r["id"] for r in results if r.get("id")]
        apply_category_label(ids, category_name)

    return results


__all__ = ["search_emails", "get_limit_defaults", "validate_category_name"]
