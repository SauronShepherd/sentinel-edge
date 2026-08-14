from sentinel_edge.exports.scanner import ExportAudience, ExportLeakScanner


def test_public_and_judge_scans_reject_private_keys_but_internal_allows() -> None:
    members = (("verification.pem", b"-----BEGIN PUBLIC KEY-----"), ("private.pem", b"-----BEGIN PRIVATE KEY-----"))
    scanner = ExportLeakScanner()
    assert scanner.scan(members, audience=ExportAudience.INTERNAL) == ()
    findings = scanner.scan(members, audience=ExportAudience.PUBLIC)
    assert any(item.category == "private_key" and item.member == "private.pem" for item in findings)
    assert any(item.category == "private_key" for item in scanner.scan(members, audience=ExportAudience.JUDGE))
