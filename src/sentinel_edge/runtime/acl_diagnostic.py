"""Optional ACL diagnostics with a hard time budget and no release-gate coupling."""
from __future__ import annotations

from dataclasses import dataclass
from queue import Empty, Queue
from threading import Thread
from typing import Callable


@dataclass(frozen=True)
class AclDiagnosticResult:
    status: str
    elapsed_budget_seconds: float
    release_gate_blocked: bool = False


def run_acl_diagnostic(check: Callable[[], str], *, timeout_seconds: float = 0.25) -> AclDiagnosticResult:
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    result: Queue[object] = Queue(maxsize=1)

    def worker() -> None:
        try:
            result.put(check(), block=False)
        except Exception as exc:  # diagnostics are best-effort by contract
            result.put(f"error:{type(exc).__name__}", block=False)

    # This diagnostic is explicitly optional and bounded. A daemon worker is
    # required because a hostile or stuck check cannot be joined at process
    # shutdown after the diagnostic budget expires.
    thread = Thread(target=worker, name="acl-diagnostic", daemon=True)
    thread.start()
    thread.join(timeout_seconds)
    try:
        status = str(result.get_nowait())
    except Empty:
        status = "timed_out"
    return AclDiagnosticResult(status=status, elapsed_budget_seconds=timeout_seconds)
