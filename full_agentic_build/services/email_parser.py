"""
Robust email parser that produces EmailRecord instances with guardrails.
Handles multipart messages, charset decoding, HTML sanitization, and attachment metadata.
"""

from __future__ import annotations

import os
import re
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from typing import Tuple, Optional, List

from bs4 import BeautifulSoup

from services.email_record import EmailRecord, AttachmentRecord
from services.email_markdown import to_markdown

# Guardrails
MAX_EMAIL_BYTES = int(os.getenv("MAX_EMAIL_BYTES", 5 * 1024 * 1024))  # 5MB default

_STRIP_TAGS = {"script", "style", "meta", "object", "iframe", "form", "link"}


def _decode_part(part: EmailMessage) -> str:
    """Decode a message part to text safely."""
    payload = part.get_payload(decode=True)
    if payload is None:
        return ""
    charset = part.get_content_charset() or "utf-8"
    try:
        return payload.decode(charset, errors="replace")
    except Exception:
        return payload.decode("utf-8", errors="replace")


def _clean_html(html: str) -> Tuple[str, str]:
    """Remove unsafe tags/attributes and return sanitized HTML plus extracted text."""
    if not html:
        return "", ""

    soup = BeautifulSoup(html, "html.parser")
    for tag in list(soup.find_all(_STRIP_TAGS)):
        tag.decompose()
    # drop images with no filename (likely trackers)
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if not src or src.startswith("cid:"):
            img.decompose()
    cleaned_html = soup.decode()
    text = soup.get_text(separator=" ")
    text = re.sub(r"\s+", " ", text).strip()
    return cleaned_html, text


def _collect_bodies(msg: EmailMessage) -> Tuple[Optional[str], Optional[str]]:
    """Return (html_body, text_body) preferring explicit parts."""
    html_body: Optional[str] = None
    text_body: Optional[str] = None

    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = part.get_content_disposition()
            if disp in ("attachment", "inline"):
                continue
            if ctype == "text/html" and html_body is None:
                html_body = _decode_part(part)
            elif ctype == "text/plain" and text_body is None:
                text_body = _decode_part(part)
    else:
        ctype = msg.get_content_type()
        if ctype == "text/html":
            html_body = _decode_part(msg)
        elif ctype == "text/plain":
            text_body = _decode_part(msg)

    return html_body, text_body


def _collect_attachments(msg: EmailMessage) -> List[AttachmentRecord]:
    atts: List[AttachmentRecord] = []
    for part in msg.iter_attachments():
        try:
            payload = part.get_payload(decode=True) or b""
            atts.append(
                AttachmentRecord(
                    filename=part.get_filename(),
                    content_type=part.get_content_type(),
                    size_bytes=len(payload),
                    is_inline=(part.get_content_disposition() == "inline"),
                    content_id=part.get("Content-ID"),
                )
            )
        except Exception:
            continue
    return atts


def parse_email_bytes(raw_bytes: bytes, source: Optional[str] = None) -> EmailRecord:
    """Parse RFC822 bytes into an EmailRecord with guardrails and sanitization."""
    if raw_bytes is None:
        raise ValueError("No email bytes provided")
    if len(raw_bytes) > MAX_EMAIL_BYTES:
        raise ValueError(f"Email exceeds size limit ({len(raw_bytes)} bytes > {MAX_EMAIL_BYTES})")

    msg = BytesParser(policy=policy.default).parsebytes(raw_bytes)

    html_body, text_body = _collect_bodies(msg)
    cleaned_html, cleaned_text_from_html = _clean_html(html_body or "")
    primary_text = text_body or cleaned_text_from_html
    body_markdown = to_markdown(
        subject=msg.get("subject", ""),
        from_addr=msg.get("from", ""),
        to_addrs=msg.get_all("to", []) or [],
        date=msg.get("date", ""),
        message_id=msg.get("message-id", ""),
        body_text=primary_text or "",
        body_html=cleaned_html or "",
    )

    attachments = _collect_attachments(msg)

    record = EmailRecord(
        uid=None,
        folder=None,
        message_id=msg.get("message-id", ""),
        path=source,
        from_addr=msg.get("from", ""),
        to=msg.get_all("to", []) or [],
        cc=msg.get_all("cc", []) or [],
        bcc=msg.get_all("bcc", []) or [],
        subject=msg.get("subject", ""),
        date=msg.get("date", ""),
        headers=dict(msg.items()),
        body_raw=html_body or text_body or "",
        body_html=cleaned_html or None,
        body_text=primary_text or None,
        body_markdown=body_markdown or None,
        eml_source=source,
        attachments=attachments,
        metadata={
            "content_type": msg.get_content_type(),
        },
    )
    return record
