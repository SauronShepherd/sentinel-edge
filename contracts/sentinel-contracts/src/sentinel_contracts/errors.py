from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Problem:
    code: str
    title: str
    detail: str = ""
    status: int = 400
    instance: str | None = None

    @classmethod
    def public(cls, code: str, title: str, safe_message: str = "", *, status: int = 400, instance: str | None = None) -> "Problem":
        return cls(code, title, safe_message[:256], status, instance)

    @classmethod
    def from_exception(cls, code: str, title: str, exception: BaseException, *, safe_message: str = "Request failed", status: int = 500) -> "Problem":
        # Exception text is intentionally not copied into the public contract.
        return cls.public(code, title, safe_message, status=status)

    def to_dict(self) -> dict[str, object]:
        result = {"type": f"https://sentinel.invalid/problems/{self.code}", "title": self.title, "status": self.status}
        if self.detail:
            lowered = self.detail.lower()
            unsafe = ("password", "secret", "token", "private_key", "api_key", "apikey", "authorization:", "bearer ", "dsn", "traceback", "file ", " at /", "internal", "private")
            result["detail"] = "Sensitive error detail redacted" if any(term in lowered for term in unsafe) else self.detail
        if self.instance: result["instance"] = self.instance
        return result
