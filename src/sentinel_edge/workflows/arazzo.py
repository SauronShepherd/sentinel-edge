"""Deterministic validation for pinned, offline Arazzo 1.1 workflow artifacts."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def validate_workflow(path: Path, *, allowed_openapi: set[str]) -> dict[str, Any]:
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if document.get("arazzo", "") != "1.1.0":
        raise ValueError("workflow must declare Arazzo 1.1.0")
    if not document.get("workflowId") or not document.get("workflows"):
        raise ValueError("workflowId and workflows are required")
    for workflow in document["workflows"]:
        required_proof = {"retry", "idempotency", "optimistic-conflict", "rest-resync"}
        if set(workflow.get("x-proof-paths", [])) != required_proof:
            raise ValueError("workflow proof must cover retry, idempotency, optimistic-conflict and rest-resync")
        for step in workflow.get("steps", []):
            operation = step.get("operationId")
            if not operation or "#" not in operation:
                raise ValueError("steps must use pinned local OpenAPI operation references")
            reference, _ = operation.split("#", 1)
            if reference not in allowed_openapi:
                raise ValueError(f"unallowlisted OpenAPI reference: {reference}")
    return document
