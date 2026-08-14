# Contributing

Use the repository registries as delivery authority. Keep Component 1 as the sole acquisition boundary and Component 4 as the sole incident-state writer. Component 6 communicates only through Component 5.

Run deterministic checks before submitting changes:

```text
python scripts/dev.py verify
python scripts/dev.py scenario
python scripts/dev.py benchmark-replay
python scripts/dev.py test-all
```

Do not add physical-hardware claims to emulation evidence, and do not add Makefile or PowerShell automation. Record changed paths and exact commands in the worklog or evidence receipt.
