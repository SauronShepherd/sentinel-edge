from dataclasses import dataclass

@dataclass
class Runtime:
    state: str = "starting"
    reason: str | None = None
    port: object | None = None
    def validate_config(self, config):
        if not isinstance(config, dict): raise ValueError("config must be an object")
    def start(self):
        if self.port is not None and getattr(self.port, "outage", False): return self.degrade()
        self.state = "ready"; self.reason = None; return self.state
    def readiness(self): return self.state == "ready"
    def health(self): return {"healthy": self.state not in {"stopped"}, "reason": self.reason}
    def degrade(self): self.state = "degraded"; self.reason = "dependency_unavailable"; return self.state
    def recover(self): return self.start()
    def drain(self, deadline): self.state = "draining"; self.reason = f"deadline:{deadline}"; return self.state
    def stop(self): self.state = "stopped"; return self.state
    def crash(self): self.state = "failed"; self.reason = "unexpected_stop"; return self.state
    def diagnostic_snapshot(self): return {"module": "collector", "state": self.state, "reason": self.reason}
