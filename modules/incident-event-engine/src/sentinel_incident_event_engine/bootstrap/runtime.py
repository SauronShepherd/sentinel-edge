from dataclasses import dataclass

@dataclass
class Runtime:
    state: str = "starting"
    reconciled: bool = False
    port: object | None = None
    def reconcile(self): self.reconciled = True
    def validate_config(self, config):
        if not isinstance(config, dict): raise ValueError("config must be an object")
    def start(self):
        if not self.reconciled: raise RuntimeError("reconciliation required before ready")
        if self.port is not None and getattr(self.port, "outage", False): return self.degrade()
        self.state = "ready"; return self.state
    def readiness(self): return self.state == "ready"
    def health(self): return {"healthy": self.state != "stopped", "reconciled": self.reconciled}
    def degrade(self): self.state = "degraded"; return self.state
    def recover(self): return self.start()
    def drain(self, deadline): self.state = "draining"; return self.state
    def stop(self): self.state = "stopped"; return self.state
    def crash(self): self.state = "failed"; return self.state
    def diagnostic_snapshot(self): return {"module": "incident", "state": self.state, "reconciled": self.reconciled}
