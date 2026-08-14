from __future__ import annotations

from dataclasses import dataclass

from sentinel_edge.analysis import AnalysisEnrichmentEngine
from sentinel_edge.collector import StreamingSourceCollector
from sentinel_edge.gateway import create_app
from sentinel_edge.incidents import IncidentEventEngine
from sentinel_edge.operations import CapabilityMatrix
from sentinel_edge.runtime import WorkloadScheduler
from sentinel_edge.scenario import DeterministicScenarioEngine


@dataclass(frozen=True)
class SentinelComponents:
    collector: StreamingSourceCollector
    analysis: AnalysisEnrichmentEngine
    runtime: WorkloadScheduler
    incidents: IncidentEventEngine
    gateway: object
    capabilities: CapabilityMatrix
    clients: str = "web-pwa-and-mobile-contract"


def compose() -> SentinelComponents:
    scenario = DeterministicScenarioEngine()
    return SentinelComponents(
        collector=scenario.collector,
        analysis=scenario.analysis,
        runtime=scenario.runtime,
        incidents=scenario.incidents,
        gateway=create_app(scenario),
        capabilities=scenario.capabilities,
    )
