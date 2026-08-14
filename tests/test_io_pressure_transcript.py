from sentinel_edge.qualification.io_pressure_transcript import IoPressureTranscript


def test_simultaneous_event_transcript_reconciles_pressure_shedding_and_deadlines() -> None:
    transcript = IoPressureTranscript(2.5, True, ("telemetry",), ("preview",), ("incident-transition:committed",))
    assert transcript.reconciled() is True
