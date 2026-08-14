from sentinel_edge.qualification.io_envelope import IoQualificationEnvelope


def test_io_envelope_allows_headline_claim_within_bounds() -> None:
    envelope = IoQualificationEnvelope(1.0, 1.0, 1.0, 1.0)
    assert envelope.evaluate(io_psi_avg10=0.5, fsync_tail_seconds=0.5, wal_checkpoint_tail_seconds=0.5, evidence_encoding_tail_seconds=0.5)["headline_claim_allowed"] is True


def test_out_of_envelope_io_stall_labels_headline_block() -> None:
    envelope = IoQualificationEnvelope(1.0, 1.0, 1.0, 1.0)
    report = envelope.evaluate(io_psi_avg10=1.5, fsync_tail_seconds=0.5, wal_checkpoint_tail_seconds=0.5, evidence_encoding_tail_seconds=0.5)
    assert report == {"within_envelope": False, "headline_claim_allowed": False, "label": "io_out_of_envelope"}
