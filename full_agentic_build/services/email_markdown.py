"""
Simple markdown converter for EmailRecord bodies.
"""

from __future__ import annotations

from typing import List
from bs4 import BeautifulSoup
import re

try:  # Optional dependency
    from markdownify import markdownify as _md_convert
except Exception:
    _md_convert = None

_HTML_SNIPPET_RE = re.compile(r"<[a-zA-Z][^>]*>")


def _looks_like_html(text: str) -> bool:
    """Return True if the text contains HTML-like tags."""
    return bool(text and _HTML_SNIPPET_RE.search(text))


def to_markdown(
    subject: str,
    from_addr: str,
    to_addrs: List[str],
    date: str,
    message_id: str,
    body_text: str,
    body_html: str = "",
) -> str:
    """Return Markdown for the email body only (headers handled elsewhere)."""
    html_for_md = body_html or (body_text if _looks_like_html(body_text) else "")
    if html_for_md:
        md_body = _html_to_markdown(html_for_md)
        if md_body:
            return md_body.strip()
    return (body_text or "").strip()


def _html_to_markdown(html: str) -> str:
    """Prefer markdownify if available; fallback to a minimal converter."""
    if _md_convert:
        try:
            return _md_convert(
                html,
                heading_style="ATX",
                bullets="-",
                strip=["script", "style", "meta", "link", "iframe", "object", "form"],
            )
        except Exception:
            pass

    soup = BeautifulSoup(html, "html.parser")

    def convert(node) -> str:
        """Recursively convert HTML nodes to markdown-like text."""
        if hasattr(node, "children"):
            tag = getattr(node, "name", "").lower()
        else:
            return str(node)

        children_md = "".join(convert(child) for child in node.children)

        if tag in ("br",):
            return "\n"
        if tag in ("p", "div", "body"):
            return children_md + "\n\n"
        if tag == "h1":
            return f"# {children_md}\n\n"
        if tag == "h2":
            return f"## {children_md}\n\n"
        if tag == "h3":
            return f"### {children_md}\n\n"
        if tag in ("strong", "b"):
            return f"**{children_md}**"
        if tag in ("em", "i"):
            return f"*{children_md}*"
        if tag == "a":
            href = node.get("href", "") or ""
            return f"[{children_md}]({href})" if href else children_md
        if tag in ("ul", "ol"):
            items = []
            for li in node.find_all("li", recursive=False):
                items.append(convert(li).strip())
            bullet = "-" if tag == "ul" else "1."
            return "\n".join(f"{bullet} {it}" for it in items) + "\n\n"
        if tag == "li":
            return f"{children_md}\n"
        # Default: just return children
        return children_md

    md = convert(soup).strip()
    return md
