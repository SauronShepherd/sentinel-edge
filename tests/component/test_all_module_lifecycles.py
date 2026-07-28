import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[2] / "apps/sentinel-module-runner/src"))
from sentinel_module_runner.main import MODULES, lifecycle

def test_every_backend_module_runs_black_box_lifecycle():
    for name in MODULES:
        states = [item["state"] for item in lifecycle(name)]
        assert states == ["ready", "degraded", "draining", "stopped"]
