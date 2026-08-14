from __future__ import annotations

import io
import zipfile

from PIL import Image

from sentinel_edge.domain.models import MediaParserProfile, MediaParserStatus, ParserIsolationState
from sentinel_edge.media import BoundedMediaParser, inspect_archive


def jpeg_with_metadata() -> bytes:
    image = Image.new("RGB", (32, 24), (200, 40, 20))
    exif = Image.Exif()
    exif[0x010E] = "sensitive source description"
    out = io.BytesIO()
    image.save(out, format="JPEG", exif=exif)
    return out.getvalue()


def test_parser_reencodes_image_and_strips_metadata() -> None:
    parser = BoundedMediaParser()
    report, sanitized = parser.parse(jpeg_with_metadata(), media_type="image/jpeg")
    assert report.status is MediaParserStatus.COMPLETED
    assert report.parser_state is ParserIsolationState.SANDBOXED
    assert report.metadata_stripped is True
    assert report.release_eligible is False
    assert report.network_namespace_proven is False
    assert sanitized is not None
    with Image.open(io.BytesIO(sanitized)) as image:
        assert image.format == "PNG"
        assert image.size == (32, 24)
        assert not image.getexif()
        assert image.info.get("exif") is None


def test_parser_rejects_unsupported_and_invalid_content() -> None:
    parser = BoundedMediaParser()
    unsupported, output = parser.parse(b"hello", media_type="text/plain")
    assert unsupported.status is MediaParserStatus.REJECTED
    assert output is None
    invalid, output = parser.parse(b"not-an-image", media_type="image/png")
    assert invalid.status is MediaParserStatus.QUARANTINED
    assert output is None
    assert "unrecognized_media_signature" in invalid.reason_codes


def test_parser_enforces_input_and_pixel_limits() -> None:
    small_profile = MediaParserProfile(maximum_input_bytes=8, maximum_pixels=100)
    parser = BoundedMediaParser(small_profile)
    oversized, output = parser.parse(b"123456789", media_type="image/png")
    assert oversized.status is MediaParserStatus.REJECTED
    assert "input_size_limit_exceeded" in oversized.reason_codes
    assert output is None

    image = Image.new("RGB", (11, 10), "white")
    data = io.BytesIO(); image.save(data, format="PNG")
    pixel_parser = BoundedMediaParser(MediaParserProfile(maximum_input_bytes=1024 * 1024, maximum_pixels=100))
    complex_report, output = pixel_parser.parse(data.getvalue(), media_type="image/png")
    assert complex_report.status is MediaParserStatus.QUARANTINED
    assert "image_complexity_limit_exceeded" in complex_report.reason_codes
    assert output is None


def test_declared_mime_is_not_trusted_over_detected_signature() -> None:
    image = Image.new("RGB", (4, 4), "blue")
    data = io.BytesIO(); image.save(data, format="PNG")
    report, output = BoundedMediaParser().parse(data.getvalue(), media_type="image/jpeg")
    assert report.status is MediaParserStatus.QUARANTINED
    assert report.detected_media_type == "image/png"
    assert "declared_media_type_mismatch" in report.reason_codes
    assert output is None


def test_archive_inspection_rejects_traversal_bombs_and_xml_entities() -> None:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as archive:
        archive.writestr("../escape.txt", "x")
        archive.writestr("doc.xml", "<!DOCTYPE x [<!ENTITY y SYSTEM 'file:///secret'>]>")
    result = inspect_archive(out.getvalue(), maximum_uncompressed_bytes=100)
    assert result["valid"] is False
    assert "archive_path_or_nesting_invalid" in result["failures"]
    assert "archive_xml_entity_declaration_rejected" in result["failures"]
