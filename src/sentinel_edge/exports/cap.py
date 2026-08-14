"""CAP 1.2 Test-draft generation and validation.

This module deliberately has no transport or send operation. CAP output produced
here is a review artifact only and is always marked ``status=Test``.
"""

from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5


CAP_NS = "urn:oasis:names:tc:emergency:cap:1.2"
ET.register_namespace("", CAP_NS)


class CapDraftValidationError(ValueError):
    """Raised when a CAP document is not a valid non-sendable Test draft."""


@dataclass(frozen=True)
class CapTestDraft:
    identifier: str
    xml: bytes
    xml_sha256: str
    status: str = "Test"
    sendable: bool = False


def _tag(name: str) -> str:
    return f"{{{CAP_NS}}}{name}"


def _required(parent: ET.Element, name: str) -> str:
    value = parent.findtext(_tag(name))
    if value is None or not value.strip():
        raise CapDraftValidationError(f"CAP field {name} is required")
    return value.strip()


def validate_cap_test_document(document: bytes | str) -> dict[str, str | bool]:
    try:
        root = ET.fromstring(document)
    except ET.ParseError as exc:
        raise CapDraftValidationError("CAP document is not well-formed XML") from exc
    if root.tag != _tag("alert"):
        raise CapDraftValidationError("CAP root must be an alert element in the CAP 1.2 namespace")
    required = {name: _required(root, name) for name in ("identifier", "sender", "sent", "status", "msgType", "scope")}
    if required["status"] != "Test":
        raise CapDraftValidationError("only CAP status=Test documents are accepted")
    if required["msgType"] not in {"Alert", "Update", "Cancel", "Ack", "Error"}:
        raise CapDraftValidationError("CAP msgType is invalid")
    if required["scope"] not in {"Public", "Restricted", "Private"}:
        raise CapDraftValidationError("CAP scope is invalid")
    try:
        datetime.fromisoformat(required["sent"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise CapDraftValidationError("CAP sent must be an ISO-8601 timestamp") from exc
    info = root.find(_tag("info"))
    if info is None:
        raise CapDraftValidationError("CAP info block is required")
    for name in ("category", "event", "urgency", "severity", "certainty"):
        _required(info, name)
    return {**required, "sendable": False}


def build_cap_test_draft(
    *,
    incident_id: UUID | str,
    sender: str,
    event: str,
    description: str,
    sent: datetime | None = None,
    category: str = "Met",
    urgency: str = "Unknown",
    severity: str = "Unknown",
    certainty: str = "Possible",
    scope: str = "Private",
) -> CapTestDraft:
    """Build a CAP 1.2 review artifact; this function never sends it."""
    if not sender.strip() or not event.strip() or not description.strip():
        raise ValueError("sender, event, and description must not be blank")
    sent = sent or datetime.now(timezone.utc)
    identifier = str(uuid5(NAMESPACE_URL, f"sentinel-cap-test:{incident_id}:{sent.isoformat()}:{event}"))
    root = ET.Element(_tag("alert"))
    fields = {
        "identifier": identifier,
        "sender": sender,
        "sent": sent.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": "Test",
        "msgType": "Alert",
        "scope": scope,
    }
    for name, value in fields.items():
        ET.SubElement(root, _tag(name)).text = value
    info = ET.SubElement(root, _tag("info"))
    for name, value in {
        "category": category,
        "event": event,
        "urgency": urgency,
        "severity": severity,
        "certainty": certainty,
        "description": description,
    }.items():
        ET.SubElement(info, _tag(name)).text = value
    xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    validated = validate_cap_test_document(xml)
    return CapTestDraft(
        identifier=validated["identifier"],
        xml=xml,
        xml_sha256=hashlib.sha256(xml).hexdigest(),
    )


def write_cap_test_draft(draft: CapTestDraft, path: str | Path) -> Path:
    """Write a CAP Test draft after revalidating it; no network side effect exists."""
    validate_cap_test_document(draft.xml)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(draft.xml)
    return target
