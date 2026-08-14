from __future__ import annotations

import asyncio
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from sentinel_edge.collaboration.factory import create_signal
from sentinel_edge.collaboration.gmail import GmailCollaborativeSignalConnector, GmailReceiptStore
from sentinel_edge.collaboration.models import CollaborationConsent, CorrelationDomain
from sentinel_edge.collaboration.wire import encode_email


class FakeGmail:
    def __init__(self, messages: dict[str, bytes]) -> None:
        self.messages = messages
        self.labels: list[tuple[str, tuple[str, ...], tuple[str, ...]]] = []

    async def list_messages(self, query: str):
        if query != 'subject:"Sentinel Collaborative Signal v1" newer_than:7d':
            raise AssertionError("unexpected Gmail fixture query")
        return [{"id": key} for key in sorted(self.messages)]

    async def get_message(self, message_id: str) -> bytes:
        return self.messages[message_id]

    async def modify_labels(self, message_id: str, *, add, remove) -> None:
        self.labels.append((message_id, tuple(add), tuple(remove)))


def build_signal(now: datetime):
    consent = CollaborationConsent(
        sharing_enabled=True,
        research_enabled=False,
        hazards={"wildfire": True, "earthquake": False, "flood": False, "landslide": False},
        policy_version="collab-demo-v1",
        updated_at=now,
    )
    signal = create_signal(
        consent=consent,
        hazard="wildfire",
        observation="possible_smoke",
        domain=CorrelationDomain(kind="observation_area", id="area:fixture"),
        node_secret="fixture-node-secret",
        episode_key="fixture-episode",
        source_mode="simulated",
        now=now,
    )
    assert signal is not None
    return signal


async def exercise() -> dict:
    now = datetime(2026, 8, 13, 12, 0, tzinfo=timezone.utc)
    signal = build_signal(now)
    raw = encode_email(signal, sender="node@example.invalid", recipient="inbox@example.invalid")
    fake = FakeGmail({"gmail-001": raw, "gmail-002": b"malformed", "gmail-003": raw})
    emitted: list[dict] = []

    async def emit(envelope: dict) -> None:
        emitted.append(envelope)

    with tempfile.TemporaryDirectory() as tmp:
        receipt_path = Path(tmp) / "gmail-receipts.json"
        first = GmailCollaborativeSignalConnector(
            client=fake,
            emit_envelope=emit,
            enabled=True,
            receipt_store=GmailReceiptStore(receipt_path),
        )
        result1 = await first.poll_once(received_at=now)
        # Reconstruct the connector from disk to prove idempotency survives a
        # process restart rather than relying on an in-memory set.
        second = GmailCollaborativeSignalConnector(
            client=fake,
            emit_envelope=emit,
            enabled=True,
            receipt_store=GmailReceiptStore(receipt_path),
        )
        result2 = await second.poll_once(received_at=now)
        receipts = json.loads(receipt_path.read_text(encoding="utf-8"))

    checks = {
        "one_valid_signal_accepted": result1.accepted == 1,
        "malformed_and_duplicate_signal_rejected": result1.rejected == 2,
        "restart_is_idempotent": result2.duplicate == 3 and result2.accepted == 0,
        "component_one_envelope_shape": len(emitted) == 1 and emitted[0].get("transport") == "email" and emitted[0].get("transport_trust") == "email_unverified",
        "durable_message_receipts": receipts.get("message_ids") == ["gmail-001", "gmail-002", "gmail-003"],
        "durable_signal_receipt": receipts.get("signal_ids") == [signal.signal_id],
        "processed_label_applied": any(row[0] == "gmail-001" and "sentinel/processed" in row[1] for row in fake.labels),
        "rejected_label_applied": any(row[0] in {"gmail-002", "gmail-003"} and "sentinel/rejected" in row[1] for row in fake.labels),
    }
    return {
        "schema": "sentinel-edge.collaboration-gmail-fixture-result.v1",
        "mode": "offline_fixture",
        "transport_trust": "email_unverified",
        "checks": checks,
        "pass": all(checks.values()),
        "first_poll": {"accepted": result1.accepted, "rejected": result1.rejected, "duplicate": result1.duplicate, "reason_codes": list(result1.reason_codes)},
        "restart_poll": {"accepted": result2.accepted, "rejected": result2.rejected, "duplicate": result2.duplicate, "reason_codes": list(result2.reason_codes)},
    }


def main() -> int:
    payload = asyncio.run(exercise())
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
