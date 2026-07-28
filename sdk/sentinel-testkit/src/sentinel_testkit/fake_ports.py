from dataclasses import dataclass, field
from collections import deque

@dataclass
class FakePort:
    values: deque = field(default_factory=deque)
    outage: bool = False
    capacity: int = 32
    corrupt: bool = False
    def send(self, value):
        if self.outage: raise TimeoutError("port unavailable")
        if len(self.values) >= self.capacity: raise TimeoutError("port capacity exceeded")
        if self.corrupt: value = {"corrupt": True}
        self.values.append(value)
    def receive(self):
        if self.outage: raise TimeoutError("port unavailable")
        return self.values.popleft() if self.values else None
    def duplicate(self, value): self.values.extend((value, value))
    def reorder(self): self.values = deque(reversed(self.values))

class CommandPort(FakePort): pass
class EventPort(FakePort): pass
class JobPort(FakePort): pass
class ArtifactPort(FakePort): pass
class ProjectionPort(FakePort): pass
