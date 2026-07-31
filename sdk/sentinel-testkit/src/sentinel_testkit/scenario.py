from dataclasses import dataclass, field
import hashlib, json
import random

@dataclass
class Scenario:
    name: str
    events: list[dict] = field(default_factory=list)
    invariants: list[str] = field(default_factory=list)
    signature: str | None = None
    transcript: list[dict] = field(default_factory=list)
    time_map: dict[str, float] = field(default_factory=dict)
    seed: int = 0
    _random: random.Random = field(init=False, repr=False)
    def __post_init__(self) -> None:
        self._random = random.Random(self.seed)
    def semantic_hash(self) -> str:
        payload = json.dumps({"name":self.name,"events":self.events,"invariants":self.invariants,"seed":self.seed,"transcript":self.transcript,"time_map":self.time_map}, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(payload).hexdigest()
    def reset(self) -> "Scenario": return Scenario(self.name, list(self.events), list(self.invariants), None, [], dict(self.time_map), self.seed)
    def sign(self, key: str) -> str:
        self.signature = hashlib.sha256((key + self.semantic_hash()).encode()).hexdigest(); return self.signature
    def record(self, event: dict) -> None: self.transcript.append(dict(event))
    def fault_choice(self, options: list[str]) -> str:
        if not options: raise ValueError("fault options cannot be empty")
        choice = self._random.choice(options)
        self.record({"fault_choice": choice})
        return choice
    def verify(self, key: str) -> bool:
        return self.signature == hashlib.sha256((key + self.semantic_hash()).encode()).hexdigest()
