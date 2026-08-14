import pytest
from pydantic import ValidationError

from sentinel_edge.qualification.adversarial import (
    AdapterDefensiveResult,
    AdversarialCampaign,
    AdversarialCase,
    DefensiveOutcome,
)


def test_campaign_records_conservative_outcome_for_each_case() -> None:
    campaign = AdversarialCampaign(results=tuple(
        AdapterDefensiveResult(
            adapter_id="collector-core",
            case=case,
            outcome=DefensiveOutcome.REJECT if case is AdversarialCase.SPOOFING else DefensiveOutcome.DEGRADE,
            reason_code=f"{case.value}_handled",
            test_id=f"TEST-AML-{case.value.upper()}",
        )
        for case in AdversarialCase
    ))
    assert {item.case for item in campaign.results} == set(AdversarialCase)


def test_campaign_rejects_missing_representative_case() -> None:
    result = AdapterDefensiveResult(
        adapter_id="collector-core", case=AdversarialCase.EVASION,
        outcome=DefensiveOutcome.ABSTAIN, reason_code="evasion_abstain", test_id="TEST-AML-EVASION"
    )
    with pytest.raises(ValidationError):
        AdversarialCampaign(results=(result,))
