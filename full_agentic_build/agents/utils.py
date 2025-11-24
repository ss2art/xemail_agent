"""Shared helpers for agent LLM interactions."""

import json
import time
from typing import Any, Callable


def invoke_with_retry(
    llm: Any,
    prompt: Any,
    max_attempts: int = 3,
    backoff_seconds: float = 0.5,
) -> Any:
    """
    Invoke the LLM with simple exponential backoff.

    Args:
        llm: LLM adapter exposing .invoke().
        prompt: Prompt or messages payload.
        max_attempts: Number of tries before surfacing the error.
        backoff_seconds: Initial backoff; doubled each retry.

    Returns:
        LLM response object.

    Raises:
        The last exception if all attempts fail.
    """
    last_exc = None
    for attempt in range(max_attempts):
        try:
            return llm.invoke(prompt)
        except Exception as exc:  # pragma: no cover - network-dependent
            last_exc = exc
            if attempt < max_attempts - 1:
                time.sleep(backoff_seconds * (2 ** attempt))
    if last_exc:
        raise last_exc
    raise RuntimeError("invoke_with_retry exhausted retries without exception")  # defensive


def parse_json_response(resp: Any, default: Any) -> Any:
    """
    Parse JSON from an LLM response, tolerating fenced/quoted content.

    Args:
        resp: Response object with optional .content attribute.
        default: Value to return on parse failure.

    Returns:
        Parsed JSON object or the provided default.
    """
    raw = getattr(resp, "content", str(resp)) or ""
    candidates = [
        raw,
        raw.strip(),
        raw.strip("`").strip(),
    ]
    for cand in candidates:
        try:
            return json.loads(cand)
        except Exception:
            continue
    return default
