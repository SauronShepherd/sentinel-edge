"""Bounded validation helpers for externally supplied interchange payloads."""
from __future__ import annotations
import xml.etree.ElementTree as ET

class XmlPayloadValidationError(ValueError):
    """Raised when XML is malformed or exceeds safe limits."""

def validate_xml_payload(document: bytes | str, *, max_bytes: int = 1_000_000, max_depth: int = 64) -> dict[str, object]:
    raw = document.encode("utf-8") if isinstance(document, str) else bytes(document)
    if len(raw) > max_bytes:
        raise XmlPayloadValidationError("XML payload exceeds byte limit")
    upper = raw.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise XmlPayloadValidationError("DTD and entity declarations are not accepted")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise XmlPayloadValidationError("XML payload is not well-formed") from exc
    depth = 0
    stack = [(root, 1)]
    while stack:
        node, current = stack.pop()
        depth = max(depth, current)
        if depth > max_depth:
            raise XmlPayloadValidationError("XML payload exceeds nesting limit")
        stack.extend((child, current + 1) for child in node)
    return {"valid": True, "root": root.tag, "bytes": len(raw), "depth": depth}
