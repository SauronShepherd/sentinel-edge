# UIX design references

This directory contains the reconstructed Sentinel Edge UIX specification, reference CSS, and generated design-reference mockups used to implement the local Judge PWA.

The PNG files under `reference-mockups/` are **design references only**. They are not screenshots from the running product and MUST NOT be used as candidate evidence or represented as runtime output. Candidate screenshots for Devpost must be captured from the frozen application build and bound in `provenance/submission-media/`.

The implemented H0 web surface lives in `src/sentinel_edge/clients/static/` and follows the same desktop workspace, split-view, inspector, table, card, status, filter, benchmark and responsive patterns while adapting the example security-console data to Sentinel Edge's four-hazard Physical AI semantics and safety boundaries.

## Reference screen catalog

The ten supplied mockups map to the following local Judge routes. The route names are the implementation contract; the reference images establish composition, spacing, hierarchy and interaction vocabulary, not product data or evidence.

| Reference | Route | Implemented surface |
|---|---|---|
| `ChatGPT Image 13 ago 2026, 13_38_14 (1).png` | `overview` | Mission Control overview |
| `ChatGPT Image 13 ago 2026, 13_38_15 (2).png` | `sites` | Sites and selected-site inspector |
| `ChatGPT Image 13 ago 2026, 13_38_15 (3).png` | `devices` | Device inventory and device inspector |
| `ChatGPT Image 13 ago 2026, 13_38_15 (4).png` | `incidents` | Incident queue and incident detail |
| `ChatGPT Image 13 ago 2026, 13_38_15 (5).png` | `investigation` | AI Investigation / Copilot workspace |
| `ChatGPT Image 13 ago 2026, 13_38_16 (6).png` | `policies` | Policy inventory and policy inspector |
| `ChatGPT Image 13 ago 2026, 13_38_16 (7).png` | `reports` | Reports and analytics |
| `ChatGPT Image 13 ago 2026, 13_38_16 (8).png` | `provisioning` | Deploy New Site wizard |
| `ChatGPT Image 13 ago 2026, 13_38_17 (9).png` | `firmware` | Firmware rollout planner |
| `ChatGPT Image 13 ago 2026, 13_38_17 (10).png` | `automation` | Automation workflow canvas |

The machine-readable screen contract in `architecture/uix-screen-contract.yaml` is generated from this catalog and `UIX_SPECIFICATION.md`. Run `python scripts/generate_uix_conformance.py` to refresh its receipt after UIX changes. For visual QA, run `python scripts/serve_demo.py`, inspect the desktop and narrow mobile layouts, and capture candidate media only after the release candidate is frozen.
