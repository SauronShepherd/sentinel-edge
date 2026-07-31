import sys
import importlib
import pytest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[2] / "apps/sentinel-module-runner/src"))
from sentinel_module_runner.main import MODULES, lifecycle, start_module

def test_every_backend_module_runs_black_box_lifecycle():
    for name in MODULES:
        states = [item["state"] for item in lifecycle(name)]
        assert states == ["ready", "degraded", "draining", "stopped"]

def test_dependency_outage_and_recovery_drive_readiness():
    for name in MODULES:
        runtime = start_module(name)
        runtime.port.outage = True
        assert runtime.start() == "degraded"
        assert runtime.readiness() is False
        runtime.port.outage = False
        assert runtime.recover() == "ready"

def test_malformed_configuration_is_rejected():
    for name in MODULES:
        runtime = importlib.import_module(MODULES[name]).Runtime()
        with pytest.raises(ValueError): runtime.validate_config([])

def test_crash_restart_and_owned_state_reconciliation():
    for name in MODULES:
        runtime = start_module(name)
        assert runtime.crash() == "failed"
        restarted = start_module(name)
        assert restarted.readiness() is True
