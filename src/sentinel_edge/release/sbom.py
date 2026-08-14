from __future__ import annotations

import importlib.metadata
import hashlib
import json
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from sentinel_edge.security import canonical_json_bytes, sha256_bytes


def _dependency_name(requirement: str) -> str:
    for marker in ("[", "<", ">", "=", "!", "~", ";", " "):
        requirement = requirement.split(marker, 1)[0]
    return requirement.strip()


def _distribution_hash(name: str) -> str | None:
    try:
        distribution = importlib.metadata.distribution(name)
    except importlib.metadata.PackageNotFoundError:
        return None
    record = distribution.read_text("RECORD")
    if record is None:
        return None
    return hashlib.sha256(record.encode("utf-8")).hexdigest()


def build_cyclonedx_sbom(root: str | Path) -> dict:
    root = Path(root).resolve()
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    dependencies = [_dependency_name(item) for item in project.get("dependencies", [])]
    components = []
    dependency_refs = []
    for name in sorted(set(dependencies), key=str.lower):
        try:
            version = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            version = "unresolved"
        ref = f"pkg:pypi/{name}@{version}"
        dependency_refs.append(ref)
        component = {
                "type": "library",
                "bom-ref": ref,
                "name": name,
                "version": version,
                "purl": ref,
                "properties": [
                    {
                        "name": "sentinel-edge:resolution-state",
                        "value": "resolved" if version != "unresolved" else "unresolved",
                    }
                ],
            }
        record_hash = _distribution_hash(name)
        if record_hash:
            component["hashes"] = [{"alg": "SHA-256", "content": record_hash}]
        components.append(component)
    app_ref = f"pkg:pypi/{project['name']}@{project['version']}"
    identity = {
        "name": project["name"],
        "version": project["version"],
        "components": components,
        "dependencies": dependency_refs,
    }
    serial = uuid5(NAMESPACE_URL, f"sentinel-edge-sbom:{sha256_bytes(canonical_json_bytes(identity))}")
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.7",
        "serialNumber": f"urn:uuid:{serial}",
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "component": {
                "type": "application",
                "bom-ref": app_ref,
                "name": project["name"],
                "version": project["version"],
                "licenses": [{"license": {"id": project.get("license", {}).get("text", "NOASSERTION")}}],
            },
            "properties": [
                {"name": "sentinel-edge:scope", "value": "declared-runtime-dependencies"},
                {
                    "name": "sentinel-edge:completeness",
                    "value": "does-not-prove-dynamic-or-os-dependency-completeness",
                },
            ],
        },
        "components": components,
        "dependencies": [{"ref": app_ref, "dependsOn": dependency_refs}],
    }


def write_cyclonedx_sbom(root: str | Path, output: str | Path | None = None) -> Path:
    root = Path(root).resolve()
    output = Path(output) if output else root / "sbom.cdx.json"
    output.write_text(json.dumps(build_cyclonedx_sbom(root), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def build_third_party_inventory(root: str | Path) -> dict:
    sbom = build_cyclonedx_sbom(root)
    packages = []
    for component in sbom["components"]:
        name = component["name"]
        version = component["version"]
        metadata = None
        try:
            metadata = importlib.metadata.metadata(name)
        except importlib.metadata.PackageNotFoundError:
            pass
        packages.append(
            {
                "name": name,
                "version": version,
                "license": (metadata.get("License") if metadata else None) or "NOASSERTION",
                "homepage": (metadata.get("Home-page") if metadata else None),
                "resolution_state": component["properties"][0]["value"],
            }
        )
    return {
        "schema": "sentinel-edge-third-party-inventory/1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "declared_runtime_dependencies",
        "limitations": [
            "This inventory does not prove operating-system, dynamically loaded, or transitive dependency completeness.",
            "NOASSERTION requires manual release review before redistribution.",
        ],
        "packages": packages,
    }


def write_third_party_inventory(root: str | Path, output: str | Path | None = None) -> Path:
    root = Path(root).resolve()
    output = Path(output) if output else root / "third-party-inventory.json"
    output.write_text(json.dumps(build_third_party_inventory(root), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def write_third_party_notices(root: str | Path, output: str | Path | None = None) -> Path:
    root = Path(root).resolve()
    inventory = build_third_party_inventory(root)
    output = Path(output) if output else root / "THIRD_PARTY_NOTICES.md"
    lines = [
        "# Third-party notices",
        "",
        "This file lists direct declared runtime dependencies. It is not a substitute for a complete transitive or operating-system inventory.",
        "",
        "| Package | Version | Declared license | Homepage |",
        "|---|---:|---|---|",
    ]
    for item in inventory["packages"]:
        lines.append(
            f"| {item['name']} | {item['version']} | {item['license']} | {item['homepage'] or ''} |"
        )
    lines.extend(
        [
            "",
            "Entries marked `NOASSERTION` require manual license verification before a public release.",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")
    return output
