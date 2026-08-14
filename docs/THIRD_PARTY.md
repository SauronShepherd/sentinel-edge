# Third-party software, models, data, and fixtures

Sentinel Edge is licensed under Apache-2.0. Third-party components retain their own licenses.

The release process generates the candidate-specific dependency inventory and CycloneDX SBOM from the pinned environment. `THIRD_PARTY_NOTICES.md` contains generated notices for declared runtime dependencies. Model, dataset, source, and fixture rights are tracked separately because a software license does not grant rights to unrelated model weights or data.

## Submission rules

- Do not add credentials, private/community reports, or raw private media to the Judge package.
- Do not present a live connector unless its authorization and terms are documented.
- Deterministic bundled fixtures must have a recorded redistribution basis.
- Optional Collaborative Detection sends only derived privacy-coarsened signals when explicitly enabled; it does not redistribute raw sensor media.
- The final public package must be rescanned for secrets and rights-sensitive assets after candidate freeze.

See `sbom.cdx.json`, `third-party-inventory.json`, `THIRD_PARTY_NOTICES.md`, and `provenance/rights-inventory.json` for machine-readable candidate evidence.
