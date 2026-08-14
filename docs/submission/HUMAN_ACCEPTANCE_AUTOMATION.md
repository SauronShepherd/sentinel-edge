# Human acceptance automation

The source acceptance plan is the complete release walkthrough referenced by the hackathon submission materials. The repository now exposes its deterministic portion as:

```bash
python scripts/dev.py human-acceptance
```

That command runs the exact-candidate cleanliness check, repository/privacy/static UIX checks, local setup/doctor/verification/demo/scenario/benchmark lanes, offline collaboration fixtures, UIX conformance, the complete strict test tree, and—unless `--local-only` is supplied—the Docker/QEMU Arm64 setup, doctor, test, demo, scenario and benchmark lanes. Use `--with-release-preflight` to append the canonical submission matrix.

The receipt is written to `qualification/human-acceptance.json`; command logs are retained under `.tmp/human-acceptance/`. A pass is fail-closed: any command or static assertion fails the receipt. The runner does not fabricate visual, keyboard, live-Gmail, screenshot/video or Devpost evidence. Those residual human/external actions remain listed explicitly in `manual_remaining` and in the final checklist.

The GitHub Actions test environment installs the same pinned test extra as local development. In particular, `jsonschema` is part of `.[test]`, `uv.lock`, `requirements-dev.lock.txt`, and the Arm64 dependency projection because the contract schema examples import it directly.
