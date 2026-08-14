from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from datetime import datetime, timezone
from typing import Any
from collections import deque
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from sentinel_edge.security.digests import canonical_json_bytes, sha256_bytes
from sentinel_edge.authority import AuthorityWatermark


class ProjectionCursor(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    stream_epoch: UUID
    authority_position: int = Field(ge=0)
    projection_version: int = Field(ge=0)
    scope_sha256: str = "unbound"

    @property
    def event_id(self) -> str:
        return f"{self.stream_epoch}:{self.authority_position}:{self.projection_version}:{self.scope_sha256}"

    @classmethod
    def parse(cls, value: str) -> "ProjectionCursor":
        parts = value.split(":")
        if len(parts) not in {3, 4}:
            raise ValueError("invalid projection cursor")
        return cls(stream_epoch=UUID(parts[0]), authority_position=int(parts[1]), projection_version=int(parts[2]), scope_sha256=parts[3] if len(parts) == 4 else "unbound")


class SignedProjection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True, serialize_by_alias=True)

    schema_id: str = Field(default="sentinel-edge-incident-projection/1.0", alias="schema")
    cursor: ProjectionCursor
    generated_at: datetime
    rebuild_state: str
    projection_lag: int = Field(ge=0)
    last_applied_authority_position: int = Field(ge=0)
    authority_watermark: AuthorityWatermark
    incidents: tuple[dict[str, Any], ...]
    command_ids: tuple[str, ...] = ()
    aggregate_versions: dict[str, int] = {}
    causation_command_ids: dict[str, tuple[str, ...]] = {}
    payload_sha256: str
    authentication_tag: str


class ProjectionClientBuffer:
    """Bounded per-client delivery queue; overflow requires REST resync."""

    def __init__(self, capacity: int = 32) -> None:
        if capacity < 1:
            raise ValueError("projection client buffer capacity must be positive")
        self.capacity = capacity
        self._items: deque[SignedProjection] = deque(maxlen=capacity)
        self._resync_required = False

    @property
    def resync_required(self) -> bool:
        return self._resync_required

    def offer(self, projection: SignedProjection) -> str:
        if self._resync_required:
            return "resync_required"
        if len(self._items) >= self.capacity:
            self._items.clear()
            self._resync_required = True
            return "resync_required"
        self._items.append(projection)
        return "queued"

    def drain(self, limit: int | None = None) -> tuple[SignedProjection, ...]:
        if self._resync_required:
            return ()
        count = len(self._items) if limit is None else max(0, limit)
        result = tuple(self._items.popleft() for _ in range(min(count, len(self._items))))
        return result

    def reset_after_resync(self) -> None:
        self._items.clear()
        self._resync_required = False


class ProjectionService:
    """Authenticated, cursor-bearing projection subordinate to authoritative REST state."""

    def __init__(self, incident_engine: Any, *, secret: bytes | None = None) -> None:
        self._engine = incident_engine
        self._secret = secret or hashlib.sha256(b"sentinel-edge-development-projection-signing-v1").digest()
        if len(self._secret) < 32:
            raise ValueError("projection signing secret must contain at least 32 bytes")
        self._stream_epoch = uuid4()
        self._rebuild_state = "ready"
        self._created_at = datetime.now(timezone.utc)

    @property
    def stream_epoch(self) -> UUID:
        return self._stream_epoch

    def rotate_epoch(self, reason: str = "projection_rebuild") -> UUID:
        if not reason.strip():
            raise ValueError("projection epoch reason must not be blank")
        self._stream_epoch = uuid4()
        self._rebuild_state = "ready"
        self._created_at = datetime.now(timezone.utc)
        return self._stream_epoch

    def _authority_position(self) -> int:
        journal = self._engine.authority_journal()
        return journal[-1].position if journal else 0

    def _projection_version(self) -> int:
        return max((item.version for item in self._engine.current()), default=0)

    def _command_ids(self) -> tuple[str, ...]:
        return tuple(str(item.command_id) for item in self._engine.command_receipts())

    def _aggregate_bindings(self) -> tuple[dict[str, int], dict[str, tuple[str, ...]]]:
        versions = {str(item.incident_id): item.version for item in self._engine.current()}
        commands: dict[str, list[str]] = {key: [] for key in versions}
        for receipt in self._engine.command_receipts():
            target = receipt.target.removeprefix("incident:")
            if target in commands:
                commands[target].append(str(receipt.command_id))
        return versions, {key: tuple(value) for key, value in commands.items()}

    def snapshot(self, *, generated_at: datetime | None = None, principal_scope: str = "", filter_scope: str = "incidents") -> SignedProjection:
        conformance = self._engine.projection_conformance()
        if not conformance["valid"]:
            raise RuntimeError("projection conformance failed: " + ",".join(conformance["failures"]))
        journal = self._engine.authority_journal()
        generated_at = generated_at or (journal[-1].accepted_at if journal else self._created_at)
        watermark = self._engine.authority_watermark()
        if not watermark.valid:
            raise RuntimeError("authority watermark is invalid: " + ",".join(watermark.failures))
        position = watermark.highest_contiguous_position
        aggregate_versions, causation_command_ids = self._aggregate_bindings()
        scope_sha256 = sha256_bytes(canonical_json_bytes({"principal": principal_scope, "filter": filter_scope}))
        cursor = ProjectionCursor(
            stream_epoch=self._stream_epoch,
            authority_position=position,
            projection_version=self._projection_version(),
            scope_sha256=scope_sha256,
        )
        payload = {
            "schema": "sentinel-edge-incident-projection/1.0",
            "cursor": cursor.model_dump(mode="json"),
            "generated_at": generated_at.isoformat(),
            "rebuild_state": self._rebuild_state,
            "projection_lag": 0,
            "last_applied_authority_position": position,
            "authority_watermark": watermark.model_dump(mode="json"),
            "incidents": [item.model_dump(mode="json") for item in self._engine.current()],
            "command_ids": list(self._command_ids()),
            "aggregate_versions": aggregate_versions,
            "causation_command_ids": {key: list(value) for key, value in causation_command_ids.items()},
        }
        digest = sha256_bytes(canonical_json_bytes(payload))
        tag = hmac.new(self._secret, canonical_json_bytes({"payload_sha256": digest, "cursor": cursor.event_id}), hashlib.sha256).hexdigest()
        return SignedProjection(
            cursor=cursor,
            generated_at=generated_at,
            rebuild_state=self._rebuild_state,
            projection_lag=0,
            last_applied_authority_position=position,
            authority_watermark=watermark,
            incidents=tuple(payload["incidents"]),
            command_ids=tuple(payload["command_ids"]),
            aggregate_versions=aggregate_versions,
            causation_command_ids=causation_command_ids,
            payload_sha256=digest,
            authentication_tag=tag,
        )

    def verify(self, projection: SignedProjection) -> bool:
        payload = {
            "schema": projection.schema_id,
            "cursor": projection.cursor.model_dump(mode="json"),
            "generated_at": projection.generated_at.isoformat(),
            "rebuild_state": projection.rebuild_state,
            "projection_lag": projection.projection_lag,
            "last_applied_authority_position": projection.last_applied_authority_position,
            "authority_watermark": projection.authority_watermark.model_dump(mode="json"),
            "incidents": list(projection.incidents),
            "command_ids": list(projection.command_ids),
            "aggregate_versions": projection.aggregate_versions,
            "causation_command_ids": {key: list(value) for key, value in projection.causation_command_ids.items()},
        }
        digest = sha256_bytes(canonical_json_bytes(payload))
        expected = hmac.new(self._secret, canonical_json_bytes({"payload_sha256": digest, "cursor": projection.cursor.event_id}), hashlib.sha256).hexdigest()
        return secrets.compare_digest(digest, projection.payload_sha256) and secrets.compare_digest(expected, projection.authentication_tag)

    def continuity(self, last_event_id: str | None, *, principal_scope: str = "", filter_scope: str = "incidents") -> tuple[str, SignedProjection]:
        current = self.snapshot(principal_scope=principal_scope, filter_scope=filter_scope)
        if not last_event_id:
            return "projection", current
        try:
            previous = ProjectionCursor.parse(last_event_id)
        except (ValueError, TypeError):
            return "resync_required", current
        if previous.stream_epoch != current.cursor.stream_epoch:
            return "resync_required", current
        if previous.scope_sha256 != current.cursor.scope_sha256:
            return "resync_required", current
        if previous.authority_position > current.cursor.authority_position:
            return "resync_required", current
        if previous.authority_position < current.cursor.authority_position - 1:
            return "resync_required", current
        return "projection", current

    @staticmethod
    def sse(event: str, projection: SignedProjection) -> str:
        data = projection.model_dump(mode="json")
        if event == "resync_required":
            data = {
                "reason": "cursor_gap_or_epoch_change",
                "rest_projection": "/v1/projections/incidents",
                "authority_watermark": projection.authority_watermark.model_dump(mode="json"),
                "current": data,
            }
        return f"id: {projection.cursor.event_id}\nevent: {event}\ndata: {json.dumps(data, sort_keys=True, separators=(',', ':'))}\n\n"
