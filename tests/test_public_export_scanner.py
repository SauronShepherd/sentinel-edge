from __future__ import annotations

from pathlib import Path

import pytest

from sentinel_edge.exports import ExportAudience, ExportLeakScanner


def test_public_export_scanner_blocks_credentials_coordinates_reporters_and_device_ids() -> None:
    scanner = ExportLeakScanner()
    payload = b'{"api_key":"SUPERSECRET123","exact_latitude":40.1,"reporter_email":"a@b.invalid","device_serial":"ABC"}'
    findings = scanner.scan((("report.json", payload),), audience=ExportAudience.JUDGE)
    categories = {item.category for item in findings}
    assert {"credential_assignment", "restricted_coordinates", "reporter_contact", "device_identifier"} <= categories
    assert scanner.scan((("report.json", payload),), audience=ExportAudience.INTERNAL) == ()


def test_public_export_scanner_blocks_raw_coordinate_precision() -> None:
    scanner = ExportLeakScanner()
    payload = b'{"latitude":40.1234567,"longitude":-3.7037901}'
    findings = scanner.scan((("judge.json", payload),), audience=ExportAudience.JUDGE)
    assert {item.category for item in findings} >= {"raw_coordinate_field", "coordinate_precision"}
