"""
Simple markdown converter for EmailRecord bodies.
"""

from __future__ import annotations

from datetime import datetime
from typing import List


def _fmt_date(date_str: str) -> str:
    try:
        # Best-effort parse common date formats; fallback to raw
        dt = datetime.fromisoformat(date_str)
        return dt.isoformat()
    except Exception:
        return date_str


def to_markdown(
    subject: str,
    from_addr: str,
    to_addrs: List[str],
    date: str,
    message_id: str,
    body_text: str,
    body_html: str = "",
) -> str:
    """Render a basic markdown version of the email."""
    lines = [
        f"# {subject or '(no subject)'}",
        "",
        f"- From: {from_addr or ''}",
        f"- To: {', '.join(to_addrs) if to_addrs else ''}",
        f"- Date: {_fmt_date(date)}",
        f"- Message-ID: {message_id or ''}",
        "",
        "---",
        "",
    ]
    content = body_text or body_html or ""
    lines.append(content.strip())
    return "\n".join(lines).strip()
