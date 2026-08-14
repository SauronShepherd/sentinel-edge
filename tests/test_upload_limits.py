import hashlib
import pytest

from sentinel_edge.qualification.upload_limits import StreamingUploadLimiter, UploadLimits


def test_streaming_upload_hashes_bytes_and_enforces_limits() -> None:
    limiter = StreamingUploadLimiter(UploadLimits(max_bytes=4, max_storage_bytes=8, max_concurrent=1))
    session = limiter.begin(media_class="image", started_at=0.0)
    session.write(b"ab", now=0.1)
    result = session.finish(now=0.2)
    assert result.accepted and result.bytes_count == 2
    assert result.sha256 == hashlib.sha256(b"ab").hexdigest()
    with pytest.raises(ValueError, match="byte_quota"):
        limiter.begin(media_class="image", started_at=1).write(b"12345", now=1)


def test_upload_limits_reject_media_time_storage_and_concurrency() -> None:
    limiter = StreamingUploadLimiter(UploadLimits(max_seconds=1, max_storage_bytes=2, max_concurrent=1))
    with pytest.raises(ValueError, match="media_class"):
        limiter.begin(media_class="video", started_at=0)
    first = limiter.begin(media_class="image", started_at=0)
    with pytest.raises(RuntimeError, match="concurrency"):
        limiter.begin(media_class="image", started_at=0)
    with pytest.raises(ValueError, match="time_quota"):
        first.write(b"a", now=2)
    first.finish(now=0)
    second = limiter.begin(media_class="image", started_at=3)
    with pytest.raises(ValueError, match="storage_quota"):
        second.write(b"123", now=3)
    second.finish(now=3)
