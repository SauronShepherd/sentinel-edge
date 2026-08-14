from sentinel_edge.geospatial.known_answers import TransformKnownAnswer, verify_known_answer


def test_known_answer_accepts_expected_non_identity_transform() -> None:
    ok, reasons = verify_known_answer(TransformKnownAnswer("horizontal", (10.1, 20.2), 0.01, True), (10.1, 20.2), input_values=(10.0, 20.0))
    assert ok and reasons == ()


def test_known_answer_rejects_tolerance_and_identity_failures() -> None:
    ok, reasons = verify_known_answer(TransformKnownAnswer("vertical", (3.0,), 0.01, True), (3.0,), input_values=(3.0,))
    assert not ok and "unexpected_identity_transform" in reasons
    ok, reasons = verify_known_answer(TransformKnownAnswer("epoch", (1.0,), 0.01), (1.2,), input_values=(0.0,))
    assert not ok and "known_answer_outside_tolerance" in reasons
