from collections import Counter

class Metrics:
    def __init__(self): self._values = Counter()
    def increment(self, name: str, amount: int = 1) -> None: self._values[name] += amount
    def snapshot(self) -> dict[str, int]: return dict(self._values)

