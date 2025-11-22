from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any


@dataclass
class AttachmentRecord:
    """Lightweight attachment descriptor safe for serialization."""

    filename: Optional[str] = None
    content_type: Optional[str] = None
    size_bytes: Optional[int] = None
    is_inline: bool = False
    content_id: Optional[str] = None
    checksum: Optional[str] = None  # e.g., sha256 for dedup/safety

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AttachmentRecord":
        return cls(**data)


@dataclass
class EmailRecord:
    """
    Canonical email representation spanning ingestion, storage, and UI.
    Designed to serialize cleanly to JSON for vector storage and caching.
    """

    # Identity / provenance
    uid: Optional[str] = None
    folder: Optional[str] = None
    message_id: Optional[str] = None
    path: Optional[str] = None  # local file path when loaded from disk

    # Headers / envelope
    from_addr: Optional[str] = None
    to: List[str] = field(default_factory=list)
    cc: List[str] = field(default_factory=list)
    bcc: List[str] = field(default_factory=list)
    subject: Optional[str] = None
    date: Optional[str] = None
    headers: Dict[str, Any] = field(default_factory=dict)

    # Bodies and variants
    body_raw: Optional[str] = None  # original selected part (html or text)
    body_text: Optional[str] = None  # normalized plain text
    body_html: Optional[str] = None  # sanitized HTML
    body_markdown: Optional[str] = None  # cleaned markdown copy
    eml_source: Optional[str] = None  # optional path or base64 of full RFC822

    # Attachments
    attachments: List[AttachmentRecord] = field(default_factory=list)

    # Misc / guardrails
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """JSON-safe dict including nested attachments."""
        data = asdict(self)
        data["attachments"] = [att.to_dict() for att in self.attachments]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmailRecord":
        """Rehydrate from a previously serialized dict."""
        attachment_dicts = data.pop("attachments", []) or []
        attachments = [AttachmentRecord.from_dict(a) for a in attachment_dicts]
        record = cls(**data)
        record.attachments = attachments
        return record
