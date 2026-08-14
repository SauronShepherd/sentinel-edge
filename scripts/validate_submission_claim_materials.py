from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "qualification/emulated-arm64-benchmark.json"
CLAIMS = ROOT / "qualification/claim-registry.json"
PUBLIC_FILES = (
    ROOT / "docs/judge-guide.md",
    ROOT / "docs/submission/DEVPOST_SUBMISSION.md",
    ROOT / "docs/submission/VIDEO_SCRIPT.md",
    ROOT / "docs/submission/VIDEO_SHOT_LIST.md",
    ROOT / "docs/submission/VIDEO_OVERLAYS.md",
    ROOT / "docs/submission/SCREENSHOT_PLAN.md",
    ROOT / "docs/release/RELEASE_NOTES.md",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _semantic_rows() -> dict[str, dict[str, float | int]]:
    payload = json.loads(BENCHMARK.read_text(encoding="utf-8"))
    if payload.get("claim_class") != "simulated":
        raise ValueError("benchmark_claim_class_not_simulated")
    if payload.get("quality_guardrails_passed") is not True:
        raise ValueError("benchmark_quality_guardrails_not_green")
    rows: dict[str, dict[str, float | int]] = {}
    for variant in ("B0", "B1", "O1"):
        semantic = payload["results"][variant]["semantic"]
        rows[variant] = {
            "median": float(semantic["median_end_to_end_ms"]),
            "p95": float(semantic["p95_end_to_end_ms"]),
            "misses": int(semantic["deadline_misses"]),
        }
    return rows


def _numbers_near_variant(text: str, variant: str) -> list[str]:
    # Capture a compact public benchmark fragment (table row, overlay, sentence,
    # or shot-list cell) without interpreting unrelated dates/versions.
    matches = re.findall(rf"\b{re.escape(variant)}\b[^\n]{{0,180}}", text, flags=re.IGNORECASE)
    return matches


def main() -> int:
    failures: list[str] = []
    try:
        rows = _semantic_rows()
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"submission claim material validation: FAIL ({exc})")
        return 1

    claim_payload = json.loads(CLAIMS.read_text(encoding="utf-8"))
    benchmark_claim = next((item for item in claim_payload.get("claims", []) if item.get("claim_id") == "benchmark-local-development"), None)
    if not isinstance(benchmark_claim, dict):
        failures.append("benchmark_claim_missing")
    else:
        if benchmark_claim.get("claim_class") != "simulated":
            failures.append("benchmark_claim_not_simulated")
        benchmark_ref = "sha256:" + _sha256(BENCHMARK)
        if benchmark_ref not in benchmark_claim.get("artifact_refs", []):
            failures.append("benchmark_claim_not_bound_to_current_benchmark")
        statement = str(benchmark_claim.get("statement", "")).lower()
        if "not raspberry pi 5 performance" not in statement:
            failures.append("benchmark_claim_pi_limitation_missing")

    for path in PUBLIC_FILES:
        if not path.is_file():
            failures.append(f"public_claim_file_missing:{path.relative_to(ROOT).as_posix()}")
            continue
        text = path.read_text(encoding="utf-8")
        fragments = {variant: _numbers_near_variant(text, variant) for variant in rows}
        if not any(fragments.values()):
            failures.append(f"public_claim_variants_missing:{path.relative_to(ROOT).as_posix()}")
            continue
        for variant, expected in rows.items():
            expected_median = f"{expected['median']:.1f}"
            expected_misses = str(expected["misses"])
            variant_fragments = fragments[variant]
            if not variant_fragments:
                failures.append(f"public_claim_variant_missing:{path.relative_to(ROOT).as_posix()}:{variant}")
                continue
            joined = " ".join(variant_fragments)
            if expected_median not in joined:
                failures.append(f"public_claim_median_mismatch:{path.relative_to(ROOT).as_posix()}:{variant}:{expected_median}")
            # Miss counts can be written as words in narrative video copy.  At
            # least one of the compact fragments must carry either the numeric
            # count or the canonical word form.
            miss_words = {0: "zero", 1: "one", 2: "two", 3: "three"}
            if expected_misses not in joined and miss_words.get(int(expected["misses"]), "") not in joined.lower():
                failures.append(f"public_claim_deadline_miss_mismatch:{path.relative_to(ROOT).as_posix()}:{variant}:{expected_misses}")
        lower = text.lower()
        if "raspberry pi" not in lower or not any(token in lower for token in ("not raspberry pi", "no raspberry pi", "not physical raspberry pi", "do not call the emulated benchmark")):
            failures.append(f"public_claim_pi_limitation_missing:{path.relative_to(ROOT).as_posix()}")
        if "simulated" not in lower and "emulated" not in lower:
            failures.append(f"public_claim_class_disclosure_missing:{path.relative_to(ROOT).as_posix()}")

    if failures:
        print("submission claim material validation: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("submission claim material validation: PASS (Claim Registry and public B0/B1/O1 materials agree)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
