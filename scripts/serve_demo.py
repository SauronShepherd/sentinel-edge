from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import uvicorn

from sentinel_edge.gateway import create_app
from sentinel_edge.scenario import DeterministicScenarioEngine, load_scenario
from sentinel_edge.security import AuthManager


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the seeded local Sentinel Edge Judge UI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--state-dir", default=".tmp/ui-demo-state")
    args = parser.parse_args()

    state_dir = ROOT / args.state_dir
    if state_dir.exists():
        shutil.rmtree(state_dir)
    scenario_path = ROOT / "fixtures/scenarios/simultaneous-event.json"
    engine = DeterministicScenarioEngine(state_dir=state_dir)
    try:
        result = engine.run(load_scenario(scenario_path))
        print(f"Seeded deterministic scenario: {result.scenario_id}")
        print(f"Sentinel Edge Judge UI: http://{args.host}:{args.port}/client")
        print("Local read-only viewer token: sentinel-dev-viewer-token")
        print("Inputs: deterministic simulated/fixture streams; physical hardware is not required.")
        uvicorn.run(create_app(engine, auth_manager=AuthManager.development()), host=args.host, port=args.port)
    finally:
        engine.close()


if __name__ == "__main__":
    main()
