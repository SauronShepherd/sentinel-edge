from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from sentinel_edge.domain.models import NotificationIntent
from sentinel_edge.storage import IncidentJournalStore

NotificationSender = Callable[[NotificationIntent], str]


@dataclass
class InMemoryIdempotentNotificationSink:
    """Deterministic test/demo sink that applies each idempotency key once."""

    receipts: dict[str, str] = field(default_factory=dict)
    effects: list[str] = field(default_factory=list)

    def send(self, intent: NotificationIntent) -> str:
        if intent.idempotency_key in self.receipts:
            return self.receipts[intent.idempotency_key]
        receipt = f"local:{len(self.receipts) + 1}:{intent.idempotency_key}"
        self.receipts[intent.idempotency_key] = receipt
        self.effects.append(intent.idempotency_key)
        return receipt


class NotificationDispatcher:
    """At-least-once dispatcher relying on stable consumer idempotency keys."""

    delivery_semantics = "at_least_once_with_idempotent_consumer"

    def __init__(self, store: IncidentJournalStore, sender: NotificationSender) -> None:
        self.store = store
        self.sender = sender

    def dispatch(self) -> tuple[NotificationIntent, ...]:
        results: list[NotificationIntent] = []
        for intent in self.store.dispatchable_notifications():
            try:
                receipt = self.sender(intent)
            except Exception as exc:  # noqa: BLE001 - provider failures become evidence, never event rollback
                results.append(
                    self.store.record_delivery(
                        str(intent.notification_id), delivered=False, error=f"{type(exc).__name__}:{exc}"
                    )
                )
            else:
                results.append(
                    self.store.record_delivery(
                        str(intent.notification_id), delivered=True, receipt_id=receipt
                    )
                )
        return tuple(results)
