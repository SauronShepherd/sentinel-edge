from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

try:
    import resource
except ImportError:  # pragma: no cover - Windows has no POSIX RLIMIT API.
    resource = None

from sentinel_edge.domain.models import (
    MediaParserProfile,
    MediaParserReport,
    MediaParserStatus,
    ParserIsolationState,
)

_CHILD = r'''
import base64, hashlib, io, json, sys
from PIL import Image, ImageOps
payload = json.loads(sys.stdin.read())
raw = base64.b64decode(payload["data"])
media_type = payload["media_type"]
maximum_pixels = int(payload["maximum_pixels"])
maximum_output_bytes = int(payload["maximum_output_bytes"])
with Image.open(io.BytesIO(raw)) as image:
    image.verify()
with Image.open(io.BytesIO(raw)) as image:
    image = ImageOps.exif_transpose(image)
    width, height = image.size
    if width <= 0 or height <= 0 or width * height > maximum_pixels:
        raise ValueError("image pixel limit exceeded")
    source_format = (image.format or "unknown").upper()
    alpha = "A" in image.getbands()
    if alpha:
        sanitized = image.convert("RGBA")
    else:
        sanitized = image.convert("RGB")
    output = io.BytesIO()
    sanitized.save(output, format="PNG", optimize=False, compress_level=9)
    data = output.getvalue()
    if len(data) > maximum_output_bytes:
        raise ValueError("sanitized image output limit exceeded")
    result = {
        "output": base64.b64encode(data).decode("ascii"),
        "output_sha256": hashlib.sha256(data).hexdigest(),
        "output_bytes": len(data),
        "width": width,
        "height": height,
        "source_format": source_format,
        "sanitized_format": "PNG",
        "alpha_preserved": alpha,
    }
    sys.stdout.write(json.dumps(result, sort_keys=True))
'''


def _limits(profile: MediaParserProfile):
    def apply() -> None:
        if resource is None:
            return
        resource.setrlimit(resource.RLIMIT_CPU, (profile.cpu_limit_seconds, profile.cpu_limit_seconds))
        memory = profile.memory_limit_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
        resource.setrlimit(resource.RLIMIT_FSIZE, (profile.maximum_output_bytes * 2, profile.maximum_output_bytes * 2))
        resource.setrlimit(resource.RLIMIT_NOFILE, (32, 32))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    return apply


class BoundedMediaParser:
    """Resource-bounded image parser producing a metadata-stripped PNG derivative.

    The process is isolated with Python isolated mode, a private temporary directory,
    reduced environment, timeout, CPU/address-space/file-size/fd limits. It does not
    claim kernel network-namespace or seccomp isolation; therefore reports are never
    release-eligible by themselves.
    """

    def __init__(self, profile: MediaParserProfile | None = None) -> None:
        self.profile = profile or MediaParserProfile()


    @staticmethod
    def _detect_media_type(data: bytes) -> str | None:
        if data.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        if data.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        return None

    def parse(self, data: bytes, *, media_type: str) -> tuple[MediaParserReport, bytes | None]:
        digest = hashlib.sha256(data).hexdigest()
        reasons: list[str] = []
        detected_media_type = self._detect_media_type(data)
        if media_type not in self.profile.allowed_media_types:
            return (
                MediaParserReport(
                    profile_id=self.profile.profile_id,
                    status=MediaParserStatus.REJECTED,
                    parser_state=ParserIsolationState.REJECTED,
                    input_sha256=digest,
                    input_bytes=len(data),
                    media_type=media_type,
                    detected_media_type=detected_media_type,
                    reason_codes=("unsupported_media_type",),
                ),
                None,
            )
        if len(data) > self.profile.maximum_input_bytes:
            return (
                MediaParserReport(
                    profile_id=self.profile.profile_id,
                    status=MediaParserStatus.REJECTED,
                    parser_state=ParserIsolationState.REJECTED,
                    input_sha256=digest,
                    input_bytes=len(data),
                    media_type=media_type,
                    detected_media_type=detected_media_type,
                    reason_codes=("input_size_limit_exceeded",),
                ),
                None,
            )
        if detected_media_type is None:
            return (
                MediaParserReport(
                    profile_id=self.profile.profile_id,
                    status=MediaParserStatus.QUARANTINED,
                    parser_state=ParserIsolationState.QUARANTINED,
                    input_sha256=digest,
                    input_bytes=len(data),
                    media_type=media_type,
                    detected_media_type=None,
                    reason_codes=("unrecognized_media_signature", "declared_media_type_not_trusted"),
                ),
                None,
            )
        if detected_media_type != media_type:
            return (
                MediaParserReport(
                    profile_id=self.profile.profile_id,
                    status=MediaParserStatus.QUARANTINED,
                    parser_state=ParserIsolationState.QUARANTINED,
                    input_sha256=digest,
                    input_bytes=len(data),
                    media_type=media_type,
                    detected_media_type=detected_media_type,
                    reason_codes=("declared_media_type_mismatch", "declared_media_type_not_trusted"),
                ),
                None,
            )
        payload = json.dumps(
            {
                "data": base64.b64encode(data).decode("ascii"),
                "media_type": media_type,
                "maximum_pixels": self.profile.maximum_pixels,
                "maximum_output_bytes": self.profile.maximum_output_bytes,
            },
            sort_keys=True,
        )
        with tempfile.TemporaryDirectory(prefix="sentinel-media-parser-") as directory:
            env = {"PYTHONHASHSEED": "0", "PATH": os.environ.get("PATH", "")}
            try:
                # POSIX keeps Python isolated because the sandbox has its
                # dependencies on the system path. The managed Windows
                # runtime installs Pillow in site-packages, which `-I`
                # intentionally hides; retain the subprocess boundary there
                # while allowing the pinned parser dependency to load.
                python_args = [sys.executable, "-I", "-c", _CHILD] if os.name == "posix" else [sys.executable, "-c", _CHILD]
                result = subprocess.run(
                    python_args,
                    input=payload,
                    text=True,
                    capture_output=True,
                    timeout=self.profile.timeout_seconds,
                    cwd=directory,
                    env=env,
                    check=False,
                    preexec_fn=_limits(self.profile) if os.name == "posix" else None,
                )
            except subprocess.TimeoutExpired:
                return (
                    MediaParserReport(
                        profile_id=self.profile.profile_id,
                        status=MediaParserStatus.QUARANTINED,
                        parser_state=ParserIsolationState.QUARANTINED,
                        input_sha256=digest,
                        input_bytes=len(data),
                        media_type=media_type,
                        detected_media_type=detected_media_type,
                        reason_codes=("parser_timeout", "network_namespace_not_proven"),
                    ),
                    None,
                )
        if result.returncode != 0:
            stderr = (result.stderr or "").lower()
            if "decompressionbomb" in stderr or "pixel limit" in stderr:
                reasons.append("image_complexity_limit_exceeded")
            elif "cannot identify image" in stderr or "unidentifiedimageerror" in stderr:
                reasons.append("invalid_image_encoding")
            else:
                reasons.append("parser_process_failed")
            reasons.append("network_namespace_not_proven")
            return (
                MediaParserReport(
                    profile_id=self.profile.profile_id,
                    status=MediaParserStatus.QUARANTINED,
                    parser_state=ParserIsolationState.QUARANTINED,
                    input_sha256=digest,
                    input_bytes=len(data),
                    media_type=media_type,
                    detected_media_type=detected_media_type,
                    reason_codes=tuple(reasons),
                ),
                None,
            )
        parsed = json.loads(result.stdout)
        sanitized = base64.b64decode(parsed["output"])
        report = MediaParserReport(
            profile_id=self.profile.profile_id,
            status=MediaParserStatus.COMPLETED,
            parser_state=ParserIsolationState.SANDBOXED,
            input_sha256=digest,
            input_bytes=len(data),
            media_type=media_type,
            detected_media_type=detected_media_type,
            output_sha256=parsed["output_sha256"],
            output_bytes=parsed["output_bytes"],
            width=parsed["width"],
            height=parsed["height"],
            source_format=parsed["source_format"],
            sanitized_format=parsed["sanitized_format"],
            metadata_stripped=True,
            alpha_preserved=parsed["alpha_preserved"],
            network_namespace_proven=False,
            release_eligible=False,
            reason_codes=(
                "metadata_stripped_by_reencode",
                "bounded_subprocess_completed",
                "network_namespace_not_proven",
                "independent_parser_review_required",
            ),
        )
        return report, sanitized

    def parse_path(self, path: str | Path, *, media_type: str) -> tuple[MediaParserReport, bytes | None]:
        return self.parse(Path(path).read_bytes(), media_type=media_type)


def inspect_archive(data: bytes, *, maximum_input_bytes: int = 32 * 1024 * 1024,
                    maximum_members: int = 256, maximum_uncompressed_bytes: int = 64 * 1024 * 1024,
                    maximum_nesting: int = 8) -> dict[str, object]:
    """Inspect an archive without extraction and fail closed on hostile content."""
    failures: list[str] = []
    if len(data) > maximum_input_bytes:
        return {"valid": False, "failures": ["archive_input_size_limit_exceeded"], "members": 0}
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            infos = archive.infolist()
            if len(infos) > maximum_members:
                failures.append("archive_member_count_limit_exceeded")
            total = 0
            for info in infos:
                name = info.filename.replace("\\", "/")
                parts = [part for part in name.split("/") if part not in ("", ".")]
                if name.startswith("/") or ".." in parts or ":" in parts[0:1] or len(parts) > maximum_nesting:
                    failures.append("archive_path_or_nesting_invalid")
                total += max(0, info.file_size)
                if total > maximum_uncompressed_bytes:
                    failures.append("archive_uncompressed_size_limit_exceeded")
                if name.lower().endswith((".xml", ".svg", ".xhtml")):
                    sample = archive.read(info, 4096).lower()
                    if b"<!doctype" in sample or b"<!entity" in sample:
                        failures.append("archive_xml_entity_declaration_rejected")
    except (OSError, zipfile.BadZipFile, RuntimeError, ValueError):
        failures.append("archive_invalid")
    return {"valid": not failures, "failures": sorted(set(failures)), "members": len(infos) if 'infos' in locals() else 0}
