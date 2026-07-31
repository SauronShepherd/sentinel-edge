from dataclasses import dataclass

@dataclass
class Runtime:
    state: str = "starting"
    qualified: bool = False
    port: object | None = None
    def qualify(self): self.qualified = True
    def validate_config(self, config):
        if not isinstance(config, dict): raise ValueError("config must be an object")
    def start(self):
        if not self.qualified: raise RuntimeError("runtime is not qualified")
        if self.port is not None and getattr(self.port, "outage", False): return self.degrade()
        self.state = "ready"; return self.state
    def readiness(self): return self.state == "ready"
    def health(self): return {"healthy": self.state != "stopped", "qualified": self.qualified}
    def degrade(self): self.state = "degraded"; return self.state
    def recover(self): return self.start()
    def drain(self, deadline): self.state = "draining"; return self.state
    def stop(self): self.state = "stopped"; return self.state
    def crash(self): self.state = "failed"; return self.state
    def diagnostic_snapshot(self): return {"module": "runtime", "state": self.state, "qualified": self.qualified}
