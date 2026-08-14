import pytest
from pydantic import ValidationError

from sentinel_edge.runtime.counterfactual import CounterfactualAudit


def test_skipped_hero_counterfactual_is_labelled_and_frozen() -> None:
    audit = CounterfactualAudit(
        opportunity_id="opp-hero-1", model_sha256="a" * 64, config_sha256="b" * 64,
        retained_input_ref="evidence:retained-1", result={"score": 0.42},
    )
    payload = audit.model_dump(mode="json")
    assert payload["diagnostic_only"] is True
    assert payload["disposition"] == "skipped"
    assert payload["model_sha256"] == "a" * 64


def test_counterfactual_cannot_be_presented_as_live_or_non_skipped() -> None:
    with pytest.raises(ValidationError):
        CounterfactualAudit(
            opportunity_id="opp-1", disposition="processed", model_sha256="a", config_sha256="b",
            diagnostic_only=False, retained_input_ref="input", result={"score": 1.0},
        )
