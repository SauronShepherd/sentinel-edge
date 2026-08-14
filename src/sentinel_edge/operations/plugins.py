from __future__ import annotations

from enum import StrEnum
from collections.abc import Iterable

from pydantic import BaseModel, ConfigDict, model_validator


class PluginCapability(StrEnum):
    COLLECT = "collect"
    ANALYZE = "analyze"
    PROJECT = "project"
    INCIDENT_LIFECYCLE = "incident_lifecycle"


class PluginLifecycle(StrEnum):
    DECLARED = "declared"
    READY = "ready"
    RUNNING = "running"
    STOPPED = "stopped"


_ALLOWED_TRANSITIONS = {
    PluginLifecycle.DECLARED: {PluginLifecycle.READY},
    PluginLifecycle.READY: {PluginLifecycle.RUNNING, PluginLifecycle.STOPPED},
    PluginLifecycle.RUNNING: {PluginLifecycle.STOPPED},
    PluginLifecycle.STOPPED: set(),
}


class PluginManifest(BaseModel):
    """Typed plugin declaration; incident authority is reserved to Component 4."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    plugin_id: str
    capabilities: tuple[PluginCapability, ...] = ()
    dependencies: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_authority(self) -> "PluginManifest":
        if not self.plugin_id.strip():
            raise ValueError("plugin_id must not be blank")
        if PluginCapability.INCIDENT_LIFECYCLE in self.capabilities and self.plugin_id != "incident":
            raise ValueError("incident lifecycle authority is reserved to the incident plugin")
        return self


def validate_plugin_graph(manifests: Iterable[PluginManifest]) -> tuple[PluginManifest, ...]:
    """Reject unknown dependencies and cycles before plugin activation."""
    items = tuple(manifests)
    graph = {item.plugin_id: item.dependencies for item in items}
    if len(graph) != len(items):
        raise ValueError("plugin identifiers must be unique")
    unknown = sorted({dependency for deps in graph.values() for dependency in deps if dependency not in graph})
    if unknown:
        raise ValueError(f"unknown plugin dependency: {unknown[0]}")
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(plugin_id: str) -> None:
        if plugin_id in visiting:
            raise ValueError("plugin dependency cycle detected")
        if plugin_id in visited:
            return
        visiting.add(plugin_id)
        for dependency in graph[plugin_id]:
            visit(dependency)
        visiting.remove(plugin_id)
        visited.add(plugin_id)

    for plugin_id in graph:
        visit(plugin_id)
    return items


def validate_plugin_transition(current: PluginLifecycle, target: PluginLifecycle) -> PluginLifecycle:
    if target not in _ALLOWED_TRANSITIONS[current]:
        raise ValueError(f"illegal plugin lifecycle transition: {current.value}->{target.value}")
    return target
