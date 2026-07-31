from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class PrivacyMinimizer:
    coordinate_precision: int = 3
    restricted_fields: frozenset[str] = frozenset({"person_id", "face", "raw_audio", "address"})

    def apply(self, metadata: dict[str, object]) -> dict[str, object]:
        result = {k: v for k, v in metadata.items() if k not in self.restricted_fields}
        for key in ("latitude", "longitude"):
            if key in result and isinstance(result[key], (int, float)): result[key] = round(float(result[key]), self.coordinate_precision)
        return result

