"""Minimal HTML-to-text extraction for fallback body parsing."""

import re

from bs4 import BeautifulSoup

def extract_text(raw_email: str) -> str:
    """
    Strip HTML markup to plain text for downstream classification.

    Args:
        raw_email: Raw HTML or text content.

    Returns:
        Plain text capped to 50k characters.
    """
    if not raw_email:
        return ""
    soup = BeautifulSoup(raw_email, "html.parser")
    text = soup.get_text(separator=" ")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:50000]
