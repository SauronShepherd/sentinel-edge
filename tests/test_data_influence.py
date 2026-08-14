from sentinel_edge.qualification.data_influence import InfluenceAction, assess_influence


def test_rights_withdrawal_blocks_promotion_and_discloses_unlearning_status() -> None:
    decision = assess_influence(artifact_id="model-v1", source_variant_id="dataset-v2", event="rights_withdrawn")
    assert decision.action is InfluenceAction.WITHDRAW
    assert decision.promotion_allowed is False
    assert decision.weight_level_removal == "unproven"


def test_corrected_labels_require_recalibration() -> None:
    decision = assess_influence(artifact_id="benchmark-v1", source_variant_id="dataset-corrected", event="labels_corrected")
    assert decision.action is InfluenceAction.RECALIBRATE
