from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
for source in (ROOT / "modules").glob("*/src"):
    sys.path.insert(0, str(source))

MODULES = {
    "collector": "sentinel_streaming_source_collector.bootstrap.runtime",
    "analyzer": "sentinel_analysis_enrichment_engine.bootstrap.runtime",
    "runtime": "sentinel_model_workload_runtime.bootstrap.runtime",
    "incident": "sentinel_incident_event_engine.bootstrap.runtime",
    "api": "sentinel_rest_api_integration_gateway.bootstrap.runtime",
}

def start_module(name: str):
    class FakeDependency:
        outage = False
    runtime = importlib.import_module(MODULES[name]).Runtime(port=FakeDependency())
    if hasattr(runtime, "qualify"): runtime.qualify()
    if hasattr(runtime, "reconcile"): runtime.reconcile()
    if hasattr(runtime, "connect_upstream"): runtime.connect_upstream()
    runtime.validate_config({})
    runtime.start()
    return runtime

def lifecycle(name: str) -> list[dict]:
    runtime = start_module(name)
    transcript = [runtime.diagnostic_snapshot()]
    runtime.degrade(); transcript.append(runtime.diagnostic_snapshot())
    runtime.start(); runtime.drain(0); transcript.append(runtime.diagnostic_snapshot())
    runtime.stop(); transcript.append(runtime.diagnostic_snapshot())
    return transcript
