"""Generate the twelve named G0 pack statuses from the active contract and H0 cutline."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/contracts/sentinel-edge-full-scope-product-contract-v0.22.0.md"
TECHNICAL_CONTRACT = ROOT / "docs/contracts/sentinel-edge-full-scope-technical-contract-v0.22.0.md"
MANIFEST = ROOT / "qualification/release-minimum-manifest.json"
OUTPUT = ROOT / "qualification/g0-gate-status.json"
PACK_RE = re.compile(r"^\| `?(G0-\d{2})`? ([^|]+) \| (.+?) \| (.+?) \|$")


def generate(root: Path = ROOT) -> dict[str, object]:
    contract = (root / CONTRACT.relative_to(ROOT)).read_text(encoding="utf-8")
    packs: list[dict[str, object]] = []
    in_table = False
    for line in contract.splitlines():
        if line.startswith("| Gate |"):
            in_table = True
            continue
        if in_table and line.startswith("|---"):
            continue
        if in_table:
            match = PACK_RE.match(line)
            if match:
                pack_id, name, required, cuttable = match.groups()
                packs.append({"id": pack_id, "name": name.strip(), "required": required.strip(), "cuttable": cuttable.strip()})
            elif line and not line.startswith("|"):
                break
    manifest = json.loads((root / MANIFEST.relative_to(ROOT)).read_text(encoding="utf-8"))
    if len(packs) != 12:
        raise ValueError(f"expected twelve G0 packs, found {len(packs)}")
    technical = (root / TECHNICAL_CONTRACT.relative_to(ROOT)).read_text(encoding="utf-8")
    pack_requirements: dict[str, set[str]] = {f"G0-{index:02d}": set() for index in range(1, 13)}
    for line in technical.splitlines():
        if not line.startswith("| FR-"):
            continue
        fields = [field.strip() for field in line.strip().strip("|").split("|")]
        if len(fields) < 7 or "`H0`" not in fields[1]:
            continue
        requirement_id = fields[0].replace("FR-", "REQ-", 1)
        pack_ids = re.findall(r"G0-\d{2}", fields[6])
        if "all g0" in fields[6].lower():
            pack_ids = list(pack_requirements)
        for pack_id in pack_ids:
            pack_requirements[pack_id].add(requirement_id)
    manifest_rows = {row["requirement_id"]: row for row in manifest["rows"]}
    release_admitted = bool(manifest["release_admitted"])
    release_profile = str(manifest.get("release_profile", "target"))
    evidence_class = "emulated_profile" if release_profile.startswith("H0-EMULATED-") else "target"
    for pack in packs:
        # Only release-registry rows are pack requirements. The technical
        # contract also contains historical/extended FR rows that are not in
        # the consolidated 743-row registry and must not appear as phantom
        # release requirements.
        requirement_ids = sorted(
            requirement_id
            for requirement_id in pack_requirements[pack["id"]]
            if requirement_id in manifest_rows
        )
        if not requirement_ids:
            raise ValueError(f"G0 pack has no mapped H0 requirements: {pack['id']}")
        rows = [manifest_rows[requirement_id] for requirement_id in requirement_ids if requirement_id in manifest_rows]
        pack.update(
            {
                "status": "pass" if release_admitted else "fail",
                "release_admitted": release_admitted,
                "evidence_class": evidence_class,
                "h0_open_count": int(manifest["open_count"]),
                "evidence_backed": release_admitted,
                "target_evidence_backed": False if evidence_class == "emulated_profile" else release_admitted,
                "requirements": requirement_ids,
                "tests": sorted({test_id for row in rows for test_id in row.get("tests", [])}),
                "artifacts": sorted(
                    {
                        "qualification/release-minimum-manifest.json",
                        "docs/contracts/sentinel-edge-full-scope-technical-contract-v0.22.0.md",
                        *{evidence_id for row in rows for evidence_id in row.get("evidence", [])},
                    }
                ),
                "mapping_source": "docs/contracts/sentinel-edge-full-scope-technical-contract-v0.22.0.md",
            }
        )
    payload = {
        "schema": "sentinel-edge.g0-gate-status.v1",
        "contract_version": "0.22.0",
        "source_contract": "docs/contracts/sentinel-edge-full-scope-product-contract-v0.22.0.md",
        "source_manifest": "qualification/release-minimum-manifest.json",
        "release_admitted": release_admitted,
        "release_profile": release_profile,
        "evidence_class": evidence_class,
        "summary": {"total": 12, "pass": sum(p["status"] == "pass" for p in packs), "fail": sum(p["status"] == "fail" for p in packs)},
        "packs": packs,
    }
    (root / OUTPUT.relative_to(ROOT)).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return payload


if __name__ == "__main__":
    payload = generate()
    print(json.dumps({
        "schema": payload["schema"],
        "release_profile": payload["release_profile"],
        "release_admitted": payload["release_admitted"],
        "summary": payload["summary"],
    }, sort_keys=True))
