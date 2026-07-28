from dataclasses import dataclass

@dataclass
class Runtime:
    state: str = "starting"
    upstream_ready: bool = False
    def connect_upstream(self): self.upstream_ready = True
    def start(self): self.state = "ready" if self.upstream_ready else "degraded"; return self.state
    def degrade(self): self.state = "degraded"; return self.state
    def drain(self): self.state = "draining"; return self.state
    def stop(self): self.state = "stopped"; return self.state
    def diagnostics(self): return {"module": "api", "state": self.state, "upstream_ready": self.upstream_ready}
