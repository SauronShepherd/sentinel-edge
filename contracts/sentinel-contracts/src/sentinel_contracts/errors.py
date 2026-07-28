from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Problem:
    code: str
    title: str
    detail: str = ""
    status: int = 400
    instance: str | None = None

    def to_dict(self) -> dict[str, object]:
        result = {"type": f"https://sentinel.invalid/problems/{self.code}", "title": self.title, "status": self.status}
        if self.detail:
            lowered = self.detail.lower()
            result["detail"] = "Sensitive error detail redacted" if any(term in lowered for term in ("password", "secret", "token", "private_key")) else self.detail
        if self.instance: result["instance"] = self.instance
        return result
