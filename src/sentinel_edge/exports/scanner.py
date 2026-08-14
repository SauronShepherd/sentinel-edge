from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable


class ExportAudience(StrEnum):
    INTERNAL = "internal"
    PUBLIC = "public"
    JUDGE = "judge"


@dataclass(frozen=True)
class LeakFinding:
    member: str
    category: str
    match: str


class ExportLeakScanner:
    """Deterministic public/Judge export scanner for high-risk leakage markers."""

    _patterns: tuple[tuple[str, re.Pattern[bytes]], ...] = (
        ("private_key", re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |)?PRIVATE KEY-----")),
        ("bearer_token", re.compile(rb"(?i)\bbearer\s+[a-z0-9._~+/=-]{12,}")),
        ("credential_assignment", re.compile(rb"(?i)\b(?:api[_-]?key|secret|password|access[_-]?token|refresh[_-]?token)\b[\"']?\s*[:=]\s*[\"']?[A-Za-z0-9._~+/=-]{8,}")),
        ("reporter_contact", re.compile(rb"(?i)\b(?:reporter_email|reporter_phone|witness_email|witness_phone)\b")),
        ("device_identifier", re.compile(rb"(?i)\b(?:device_serial|hardware_serial|machine_id|boot_id|mac_address)\b")),
        ("mac_address", re.compile(rb"(?i)\b(?:[0-9a-f]{2}:){5}[0-9a-f]{2}\b")),
        ("restricted_coordinates", re.compile(rb"(?i)\b(?:exact_latitude|exact_longitude|restricted_coordinates|private_location)\b")),
        ("raw_coordinate_field", re.compile(rb'(?i)["\'](?:latitude|longitude|lat|lon)["\']\s*:\s*-?\d{1,3}\.\d{5,}')),
        ("coordinate_precision", re.compile(rb"(?i)\b(?:latitude|longitude|lat|lon)\b[^\n]{0,32}-?\d{1,3}\.\d{5,}")),
        ("nonredistributable_marker", re.compile(rb"(?i)\b(?:nonredistributable|no_redistribution|reference_only_content)\b")),
    )

    def scan(self, members: Iterable[tuple[str, bytes]], *, audience: ExportAudience) -> tuple[LeakFinding, ...]:
        if audience is ExportAudience.INTERNAL:
            return ()
        findings: list[LeakFinding] = []
        for member, data in members:
            sample = data[: 4 * 1024 * 1024]
            for category, pattern in self._patterns:
                for match in pattern.finditer(sample):
                    token = match.group(0)[:96].decode("utf-8", errors="replace")
                    findings.append(LeakFinding(member=member, category=category, match=token))
        return tuple(findings)
