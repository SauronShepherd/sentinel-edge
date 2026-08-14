from __future__ import annotations

from typing import Protocol
from pydantic import BaseModel, ConfigDict

from sentinel_edge.domain.models import AnalysisResult, Observation


class HazardAdapter(Protocol):
    adapter_id: str

    def analyze(self, observation: Observation) -> AnalysisResult: ...


class HazardExtensionManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    hazard: str
    owner: str
    version: str
    adapter_id: str
    input_schema: str
    output_schema: str
    test_module: str

    @classmethod
    def catalog(cls) -> tuple["HazardExtensionManifest", ...]:
        return tuple(cls(hazard=name, owner="component-2-analysis", version="1.0.0",
                         adapter_id=adapter, input_schema="sentinel-edge-observation/1.0",
                         output_schema="sentinel-edge-analysis/1.0", test_module=module)
                     for name, adapter, module in (
                         ("earthquake", "earthquake-int8-1d-v1", "tests/test_hazards.py"),
                         ("flood", "flood-v2", "tests/test_flood_landslide_contracts.py"),
                         ("wildfire", "wildfire-v2", "tests/test_hazards.py"),
                         ("landslide", "landslide-v2", "tests/test_flood_landslide_contracts.py"),
                     ))
