from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "docs/plans/sentinel-edge-complete-end-to-end-build-plan-v0.13.0.md"
LEDGER = ROOT / "provenance/requirements/i00-i02-ledger.yaml"

rows = {}
for line in PLAN.read_text(encoding="utf-8").splitlines():
    match = re.match(r"\| `(I\d{2}-S\d{2}-T\d{2})` \| `([^`]+)` \|", line)
    if match:
        rows[match.group(1)] = match.group(2)

text = LEDGER.read_text(encoding="utf-8")
for task_id, path in rows.items():
    if f"- id: {task_id}\n" not in text:
        continue
    exists = (ROOT / path).exists()
    status = "VERIFIED" if exists else "IMPLEMENTED_UNVERIFIED"
    pattern = rf"(- id: {re.escape(task_id)}\n\s+status: )\S+"
    text, count = re.subn(pattern, rf"\g<1>{status}", text, count=1)
    if count != 1:
        raise SystemExit(f"could not update {task_id}")
    block = re.search(rf"- id: {re.escape(task_id)}(?P<body>.*?)(?=\n  - id:|\Z)", text, re.DOTALL)
    if not block:
        raise SystemExit(f"could not locate {task_id}")
    body = block.group("body")
    body = re.sub(r'description: "[^"]*"', f'description: "{task_id}: {path}"', body, count=1)
    body = re.sub(r"implementation_paths: \[\]", f"implementation_paths: [{path}]", body, count=1)
    text = text[: block.start("body")] + body + text[block.end("body"):]

LEDGER.write_text(text, encoding="utf-8", newline="\n")
print(f"reconciled {sum(1 for task_id in rows if f'- id: {task_id}\n' in text)} task mappings")
