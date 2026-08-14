from pathlib import Path

import pytest

from sentinel_edge.qualification.upload_quarantine import QuarantineStream


def test_upload_stream_is_chunk_bounded_and_atomically_quarantined(tmp_path: Path) -> None:
    stream = QuarantineStream(tmp_path, max_chunk_bytes=3)
    stream.begin()
    stream.write(b"ab")
    with pytest.raises(ValueError, match="backpressure"):
        stream.write(b"1234")
    final, digest = stream.complete()
    assert final.parent == (tmp_path / ".quarantine").resolve()
    assert final.read_bytes() == b"ab"
    assert len(digest) == 64


def test_aborted_upload_is_removed_from_quarantine(tmp_path: Path) -> None:
    stream = QuarantineStream(tmp_path)
    stream.begin()
    stream.write(b"partial")
    stream.abort()
    assert list((tmp_path / ".quarantine").glob(".tmp-upload-*")) == []
