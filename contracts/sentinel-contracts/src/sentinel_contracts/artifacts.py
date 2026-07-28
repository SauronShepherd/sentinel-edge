from dataclasses import dataclass
from enum import StrEnum
import re

class PrivacyClass(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    RESTRICTED = "restricted"

@dataclass(frozen=True, slots=True)
class ArtifactRef:
    digest: str
    media_type: str
    owner: str
    privacy: PrivacyClass = PrivacyClass.INTERNAL

    def __post_init__(self) -> None:
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", self.digest): raise ValueError("digest must be sha256 content address")
        if not re.fullmatch(r"[a-z][a-z0-9-]{1,30}", self.owner): raise ValueError("invalid owner namespace")
