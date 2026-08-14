import pytest

from sentinel_edge.qualification.media_lead import MediaLead, MediaLeadDisposition


def test_media_lead_keeps_embed_metadata_separate_from_bytes() -> None:
    lead = MediaLead(platform="YouTube", canonical_url="https://video.example/watch/1",
        disposition=MediaLeadDisposition.METADATA_ONLY)
    assert lead.media_bytes_retained is False


def test_lawful_supplied_media_requires_enrollment_and_download_is_blocked() -> None:
    upload = MediaLead(platform="supplied", canonical_url="https://upload.example/1",
        disposition=MediaLeadDisposition.SUPPLIED_MEDIA_UPLOAD, enrollment_id="enrol-1", media_bytes_retained=True)
    assert upload.media_bytes_retained is True
    with pytest.raises(ValueError):
        MediaLead(platform="YouTube", canonical_url="https://video.example/watch/1",
            disposition=MediaLeadDisposition.DOWNLOAD_BLOCKED, media_bytes_retained=True)
