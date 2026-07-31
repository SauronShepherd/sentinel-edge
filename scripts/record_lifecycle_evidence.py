from __future__ import annotations
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps/sentinel-module-runner/src"))
from sentinel_module_runner.main import MODULES, start_module
import importlib

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "provenance/iterations/I02/evidence/lifecycle-matrix.json"

def run(name: str) -> dict:
    module = importlib.import_module(MODULES[name])
    invalid = module.Runtime()
    malformed = False
    try: invalid.validate_config([])
    except ValueError: malformed = True
    runtime = start_module(name)
    ready = runtime.readiness()
    runtime.port.outage = True; degraded = runtime.start() == "degraded"
    runtime.port.outage = False; recovered = runtime.recover() == "ready"
    draining = runtime.drain(0) == "draining"
    stopped = runtime.stop() == "stopped"
    restarted = start_module(name).readiness()
    crashed = runtime.crash() == "failed"
    post_crash_restart = start_module(name).readiness()
    return {"module": name, "malformed_config_rejected": malformed, "ready": ready, "degraded_on_outage": degraded, "recovered": recovered, "draining": draining, "stopped": stopped, "restart_ready": restarted, "crashed": crashed, "post_crash_restart_ready": post_crash_restart}

def main() -> int:
    records = [run(name) for name in MODULES]
    if not all(all(record.values()) for record in records): print("lifecycle evidence: FAIL"); return 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes((json.dumps({"scenarios": records}, indent=2, sort_keys=True) + "\n").encode())
    print("lifecycle evidence: PASS (5 modules)"); return 0

if __name__ == "__main__": raise SystemExit(main())
