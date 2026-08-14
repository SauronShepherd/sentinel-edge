"""Derived translation artifact retaining original evidence semantics."""

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DerivedTranslation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    artifact_id: str
    original_text: str
    original_language: str
    translated_text: str
    target_language: str
    translation_confidence: float = Field(ge=0.0, le=1.0)
    model_version: str
    source_evidence_id: str
    derived: bool = True

    @model_validator(mode="after")
    def validate_translation(self) -> "DerivedTranslation":
        if any(not value.strip() for value in (self.artifact_id, self.original_text, self.original_language,
                                                self.translated_text, self.target_language, self.model_version,
                                                self.source_evidence_id)):
            raise ValueError("translation artifact and provenance fields are required")
        if self.original_language == self.target_language:
            raise ValueError("translation target must differ from original language")
        return self
