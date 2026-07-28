from dataclasses import dataclass

@dataclass
class Runtime:
    state: str = "starting"
    reconciled: bool = False
    def reconcile(self): self.reconciled = True
    def start(self):
        if not self.reconciled: raise RuntimeError("reconciliation required before ready")
        self.state = "ready"; return self.state
    def degrade(self): self.state = "degraded"; return self.state
    def drain(self): self.state = "draining"; return self.state
    def stop(self): self.state = "stopped"; return self.state
    def diagnostics(self): return {"module": "incident", "state": self.state, "reconciled": self.reconciled}
