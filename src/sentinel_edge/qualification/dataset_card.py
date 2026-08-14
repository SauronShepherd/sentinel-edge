"""Dataset card licence separation for downloadable assets."""

from pydantic import BaseModel, ConfigDict, model_validator


class DatasetCard(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    dataset_id: str
    dataset_name: str
    downloadable_asset_license: str
    provenance: str
    article_license: str | None = None
    code_license: str | None = None
    model_license: str | None = None

    @model_validator(mode="after")
    def validate_card(self) -> "DatasetCard":
        if any(not value.strip() for value in (self.dataset_id, self.dataset_name,
                                                self.downloadable_asset_license, self.provenance)):
            raise ValueError("dataset card identity, asset licence, and provenance are required")
        if self.downloadable_asset_license.upper() in {"NOASSERTION", "UNKNOWN"}:
            raise ValueError("downloadable asset licence must be resolved")
        return self
