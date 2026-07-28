from dataclasses import dataclass, field
from collections import deque

@dataclass
class FakePort:
    values: deque = field(default_factory=deque)
    outage: bool = False
    def send(self, value):
        if self.outage: raise TimeoutError("port unavailable")
        self.values.append(value)
    def receive(self):
        if self.outage: raise TimeoutError("port unavailable")
        return self.values.popleft() if self.values else None
    def duplicate(self, value): self.values.extend((value, value))
