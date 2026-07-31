from dataclasses import dataclass
import hashlib

@dataclass(frozen=True, slots=True)
class DeduplicationDecision:
    identity: str
    action: str

def identity(source_id: str, sequence: int | str, payload: bytes | str) -> str:
    raw = f"{source_id}\0{sequence}\0".encode() + (payload if isinstance(payload, bytes) else payload.encode())
    return "sha256:" + hashlib.sha256(raw).hexdigest()

def decide(identity_key: str, seen: set[str], replace_latest: bool = False) -> DeduplicationDecision:
    if identity_key in seen: return DeduplicationDecision(identity_key, "replace" if replace_latest else "duplicate")
    return DeduplicationDecision(identity_key, "accept")

