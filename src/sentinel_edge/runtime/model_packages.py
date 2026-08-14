from __future__ import annotations

import ast
import json
import math
import os
import stat
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from sentinel_edge.security import canonical_json_bytes, sha256_bytes, sha256_file


ONNX_WORKER_MAX_ADDRESS_SPACE_BYTES = 512 * 1024 * 1024
ONNX_WORKER_MAX_FILE_DESCRIPTORS = 64


def onnx_worker_policy() -> dict[str, Any]:
    """Return the portable worker contract used for target qualification."""
    return {
        "timeout_seconds": 5.0,
        "cpu_seconds": 6,
        "address_space_bytes": ONNX_WORKER_MAX_ADDRESS_SPACE_BYTES,
        "file_descriptors": ONNX_WORKER_MAX_FILE_DESCRIPTORS,
        "process_group_isolated": os.name == "posix" or hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"),
        "close_fds": True,
        "network_policy": "inheritance must be denied by target service sandbox",
    }

_DTYPE_INFO: dict[int, tuple[str, int | None]] = {
    1: ("float32", 4),
    2: ("uint8", 1),
    3: ("int8", 1),
    4: ("uint16", 2),
    5: ("int16", 2),
    6: ("int32", 4),
    7: ("int64", 8),
    8: ("string", None),
    9: ("bool", 1),
    10: ("float16", 2),
    11: ("float64", 8),
    12: ("uint32", 4),
    13: ("uint64", 8),
    14: ("complex64", 8),
    15: ("complex128", 16),
    16: ("bfloat16", 2),
    17: ("float8e4m3fn", 1),
    18: ("float8e4m3fnuz", 1),
    19: ("float8e5m2", 1),
    20: ("float8e5m2fnuz", 1),
}


class ProtobufParseError(ValueError):
    pass


@dataclass
class _ParseBudget:
    max_total_bytes: int = 32 * 1024 * 1024
    max_fields: int = 100_000
    max_depth: int = 16
    max_string_bytes: int = 4096
    max_nodes: int = 100_000
    max_initializers: int = 100_000
    max_attributes: int = 200_000
    fields_seen: int = 0
    nodes_seen: int = 0
    initializers_seen: int = 0
    attributes_seen: int = 0

    def consume(self, *, depth: int) -> None:
        if depth > self.max_depth:
            raise ProtobufParseError("protobuf_recursion_limit_exceeded")
        self.fields_seen += 1
        if self.fields_seen > self.max_fields:
            raise ProtobufParseError("protobuf_field_limit_exceeded")

    def consume_node(self) -> None:
        self.nodes_seen += 1
        if self.nodes_seen > self.max_nodes:
            raise ProtobufParseError("onnx_node_limit_exceeded")

    def consume_initializer(self) -> None:
        self.initializers_seen += 1
        if self.initializers_seen > self.max_initializers:
            raise ProtobufParseError("onnx_initializer_limit_exceeded")

    def consume_attribute(self) -> None:
        self.attributes_seen += 1
        if self.attributes_seen > self.max_attributes:
            raise ProtobufParseError("onnx_attribute_limit_exceeded")


def _read_varint(data: bytes, offset: int) -> tuple[int, int]:
    value = 0
    shift = 0
    for _ in range(10):
        if offset >= len(data):
            raise ProtobufParseError("truncated_varint")
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, offset
        shift += 7
    raise ProtobufParseError("oversized_varint")


def _iter_fields(data: bytes, budget: _ParseBudget, *, depth: int = 0) -> Iterable[tuple[int, int, int | bytes]]:
    if len(data) > budget.max_total_bytes:
        raise ProtobufParseError("protobuf_message_too_large")
    offset = 0
    while offset < len(data):
        budget.consume(depth=depth)
        key, offset = _read_varint(data, offset)
        field = key >> 3
        wire = key & 7
        if field <= 0:
            raise ProtobufParseError("invalid_protobuf_field_number")
        if wire == 0:
            value, offset = _read_varint(data, offset)
            yield field, wire, value
        elif wire == 1:
            if offset + 8 > len(data):
                raise ProtobufParseError("truncated_fixed64")
            yield field, wire, data[offset : offset + 8]
            offset += 8
        elif wire == 2:
            length, offset = _read_varint(data, offset)
            end = offset + length
            if end > len(data):
                raise ProtobufParseError("truncated_length_delimited")
            yield field, wire, data[offset:end]
            offset = end
        elif wire == 5:
            if offset + 4 > len(data):
                raise ProtobufParseError("truncated_fixed32")
            yield field, wire, data[offset : offset + 4]
            offset += 4
        else:
            raise ProtobufParseError(f"unsupported_wire_type:{wire}")


def _decode_text(value: bytes, budget: _ParseBudget) -> str:
    if len(value) > budget.max_string_bytes:
        raise ProtobufParseError("protobuf_string_too_large")
    try:
        return value.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ProtobufParseError("protobuf_string_not_utf8") from exc


class DimensionBound(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    minimum: int = Field(ge=1)
    maximum: int = Field(ge=1)
    symbol: str | None = None

    @model_validator(mode="after")
    def validate_bound(self) -> "DimensionBound":
        if self.maximum < self.minimum:
            raise ValueError("dimension maximum must be >= minimum")
        if self.symbol is not None and not self.symbol.strip():
            raise ValueError("dimension symbol must not be blank")
        return self


class TensorAllocationContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    dtype: str
    rank: int = Field(ge=0, le=16)
    dimensions: tuple[DimensionBound, ...]
    maximum_elements: int = Field(ge=1)
    maximum_bytes: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_allocation(self) -> "TensorAllocationContract":
        if not self.name.strip() or not self.dtype.strip():
            raise ValueError("tensor contract name and dtype must not be blank")
        if self.rank != len(self.dimensions):
            raise ValueError("tensor rank must equal the number of dimensions")
        computed = math.prod(item.maximum for item in self.dimensions) if self.dimensions else 1
        if computed != self.maximum_elements:
            raise ValueError("maximum_elements must equal the product of dimension maxima")
        width = next((size for name, size in _DTYPE_INFO.values() if name == self.dtype), None)
        if width is None:
            raise ValueError("release tensor dtype must have a finite byte width")
        if computed * width != self.maximum_bytes:
            raise ValueError("maximum_bytes must equal maximum_elements times dtype width")
        return self


class PackageFile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str
    sha256: str
    bytes: int = Field(ge=0)

    @field_validator("path")
    @classmethod
    def safe_path(cls, value: str) -> str:
        path = PurePosixPath(value)
        if path.is_absolute() or ".." in path.parts or not value.strip() or "://" in value:
            raise ValueError("package file path must be safe and relative")
        return path.as_posix()


class ModelPackageManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_: Literal["sentinel-edge-model-package-manifest/1.0"] = Field(
        default="sentinel-edge-model-package-manifest/1.0", alias="schema", serialization_alias="schema"
    )
    package_id: str
    model_path: str
    model_sha256: str
    model_format: Literal["onnx"] = "onnx"
    release_root: str
    package_files: tuple[PackageFile, ...]
    inputs: tuple[TensorAllocationContract, ...]
    outputs: tuple[TensorAllocationContract, ...]
    allowed_opsets: dict[str, tuple[int, int]]
    allowed_operators: dict[str, tuple[str, ...]]
    allowed_custom_domains: tuple[str, ...] = ()
    external_data_allowed: bool = False
    allowed_external_data: tuple[str, ...] = ()
    control_flow_allowed: bool = False
    python_ops_allowed: bool = False
    custom_op_libraries: tuple[str, ...] = ()
    runtime_extensions: tuple[str, ...] = ()
    plugin_execution_providers: tuple[str, ...] = ()
    expected_execution_provider: str
    fallback_allowed: bool = False
    created_at: datetime
    expires_at: datetime

    @model_validator(mode="after")
    def validate_manifest(self) -> "ModelPackageManifest":
        for value in (self.package_id, self.model_path, self.release_root, self.expected_execution_provider):
            if not value.strip():
                raise ValueError("model package fields must not be blank")
        if self.expires_at <= self.created_at:
            raise ValueError("model package manifest must expire after creation")
        paths = [item.path for item in self.package_files]
        if len(paths) != len(set(paths)):
            raise ValueError("model package file paths must be unique")
        if self.model_path not in paths:
            raise ValueError("model_path must be declared in package_files")
        if set(self.allowed_external_data) - set(paths):
            raise ValueError("allowed external data must be declared package files")
        if self.python_ops_allowed:
            raise ValueError("release profile cannot enable Python operators")
        if self.custom_op_libraries or self.runtime_extensions or self.plugin_execution_providers:
            raise ValueError("unqualified executable extensions are prohibited")
        if not self.inputs or not self.outputs:
            raise ValueError("release model requires input and output contracts")
        return self


class RuntimeAdmissionContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    runtime_name: str
    runtime_version: str
    execution_provider: str
    compiler: str
    architecture: str
    runtime_package_sha256: str
    target_host_qualified: bool = False
    target_runtime_measured: bool = False
    provider_assignment_proven: bool = False
    fallback_observed: bool = False


@dataclass(frozen=True)
class _TensorShape:
    name: str
    dtype: str
    dimensions: tuple[int | str | None, ...]


@dataclass(frozen=True)
class _TensorInitializer:
    name: str
    dtype: str
    dimensions: tuple[int, ...]
    external_data: tuple[tuple[str, str], ...]
    external_location: bool
    raw_bytes: int


@dataclass(frozen=True)
class _Node:
    path: str
    domain: str
    operator: str
    attributes_sha256: str
    has_subgraph: bool


def _parse_dimension(data: bytes, budget: _ParseBudget, depth: int) -> int | str | None:
    result: int | str | None = None
    for field, wire, value in _iter_fields(data, budget, depth=depth):
        if field == 1 and wire == 0:
            result = int(value)
        elif field == 2 and wire == 2:
            result = _decode_text(value, budget)
    return result


def _parse_value_info(data: bytes, budget: _ParseBudget, depth: int) -> _TensorShape:
    name = ""
    dtype = "unknown"
    dims: tuple[int | str | None, ...] = ()
    for field, wire, value in _iter_fields(data, budget, depth=depth):
        if field == 1 and wire == 2:
            name = _decode_text(value, budget)
        elif field == 2 and wire == 2:
            for t_field, t_wire, t_value in _iter_fields(value, budget, depth=depth + 1):
                if t_field != 1 or t_wire != 2:
                    continue
                elem_type = 0
                parsed_dims: list[int | str | None] = []
                for tt_field, tt_wire, tt_value in _iter_fields(t_value, budget, depth=depth + 2):
                    if tt_field == 1 and tt_wire == 0:
                        elem_type = int(tt_value)
                    elif tt_field == 2 and tt_wire == 2:
                        for s_field, s_wire, s_value in _iter_fields(tt_value, budget, depth=depth + 3):
                            if s_field == 1 and s_wire == 2:
                                parsed_dims.append(_parse_dimension(s_value, budget, depth + 4))
                dtype = _DTYPE_INFO.get(elem_type, (f"onnx_dtype_{elem_type}", None))[0]
                dims = tuple(parsed_dims)
    return _TensorShape(name=name, dtype=dtype, dimensions=dims)


def _parse_string_entry(data: bytes, budget: _ParseBudget, depth: int) -> tuple[str, str]:
    key = value_text = ""
    for field, wire, value in _iter_fields(data, budget, depth=depth):
        if field == 1 and wire == 2:
            key = _decode_text(value, budget)
        elif field == 2 and wire == 2:
            value_text = _decode_text(value, budget)
    return key, value_text


def _parse_tensor(data: bytes, budget: _ParseBudget, depth: int) -> _TensorInitializer:
    dims: list[int] = []
    dtype_number = 0
    name = ""
    raw_bytes = 0
    external: list[tuple[str, str]] = []
    external_location = False
    for field, wire, value in _iter_fields(data, budget, depth=depth):
        if field == 1 and wire == 0:
            dims.append(int(value))
        elif field == 1 and wire == 2:
            offset = 0
            while offset < len(value):
                item, offset = _read_varint(value, offset)
                dims.append(int(item))
        elif field == 2 and wire == 0:
            dtype_number = int(value)
        elif field == 8 and wire == 2:
            name = _decode_text(value, budget)
        elif field == 9 and wire == 2:
            raw_bytes = len(value)
        elif field == 13 and wire == 2:
            external.append(_parse_string_entry(value, budget, depth + 1))
        elif field == 14 and wire == 0:
            external_location = int(value) == 1
    return _TensorInitializer(
        name=name,
        dtype=_DTYPE_INFO.get(dtype_number, (f"onnx_dtype_{dtype_number}", None))[0],
        dimensions=tuple(dims),
        external_data=tuple(external),
        external_location=external_location,
        raw_bytes=raw_bytes,
    )


def _parse_node(data: bytes, budget: _ParseBudget, *, path: str, depth: int) -> tuple[_Node, tuple[_Node, ...]]:
    budget.consume_node()
    domain = ""
    operator = ""
    attributes: list[bytes] = []
    nested: list[_Node] = []
    has_subgraph = False
    for field, wire, value in _iter_fields(data, budget, depth=depth):
        if field == 4 and wire == 2:
            operator = _decode_text(value, budget)
        elif field == 7 and wire == 2:
            domain = _decode_text(value, budget)
        elif field == 5 and wire == 2:
            budget.consume_attribute()
            attributes.append(value)
            attr_name = ""
            graph_messages: list[bytes] = []
            for a_field, a_wire, a_value in _iter_fields(value, budget, depth=depth + 1):
                if a_field == 1 and a_wire == 2:
                    attr_name = _decode_text(a_value, budget)
                elif a_field in {6, 11} and a_wire == 2:
                    graph_messages.append(a_value)
            for index, graph_message in enumerate(graph_messages):
                has_subgraph = True
                graph = _parse_graph(graph_message, budget, path=f"{path}/attr:{attr_name or 'anonymous'}:{index}", depth=depth + 2)
                nested.extend(graph[0])
    normalized_domain = domain or "ai.onnx"
    node = _Node(
        path=path,
        domain=normalized_domain,
        operator=operator,
        attributes_sha256=sha256_bytes(b"".join(sorted(attributes))),
        has_subgraph=has_subgraph,
    )
    return node, tuple(nested)


def _parse_graph(
    data: bytes, budget: _ParseBudget, *, path: str = "graph", depth: int = 0
) -> tuple[tuple[_Node, ...], tuple[_TensorInitializer, ...], tuple[_TensorShape, ...], tuple[_TensorShape, ...]]:
    nodes: list[_Node] = []
    initializers: list[_TensorInitializer] = []
    inputs: list[_TensorShape] = []
    outputs: list[_TensorShape] = []
    node_index = 0
    for field, wire, value in _iter_fields(data, budget, depth=depth):
        if field == 1 and wire == 2:
            node, nested = _parse_node(value, budget, path=f"{path}/node:{node_index}", depth=depth + 1)
            nodes.append(node)
            nodes.extend(nested)
            node_index += 1
        elif field == 5 and wire == 2:
            budget.consume_initializer()
            initializers.append(_parse_tensor(value, budget, depth + 1))
        elif field == 11 and wire == 2:
            inputs.append(_parse_value_info(value, budget, depth + 1))
        elif field == 12 and wire == 2:
            outputs.append(_parse_value_info(value, budget, depth + 1))
    return tuple(nodes), tuple(initializers), tuple(inputs), tuple(outputs)


def inspect_onnx_graph(path: str | Path) -> dict[str, Any]:
    model_path = Path(path)
    data = model_path.read_bytes()
    budget = _ParseBudget(max_total_bytes=max(len(data), 1))
    ir_version = 0
    opsets: list[dict[str, Any]] = []
    graph_payload: bytes | None = None
    functions = 0
    for field, wire, value in _iter_fields(data, budget):
        if field == 1 and wire == 0:
            ir_version = int(value)
        elif field == 7 and wire == 2:
            if graph_payload is not None:
                raise ProtobufParseError("multiple_model_graphs")
            graph_payload = value
        elif field == 8 and wire == 2:
            domain = "ai.onnx"
            version = 0
            for o_field, o_wire, o_value in _iter_fields(value, budget, depth=1):
                if o_field == 1 and o_wire == 2:
                    domain = _decode_text(o_value, budget) or "ai.onnx"
                elif o_field == 2 and o_wire == 0:
                    version = int(o_value)
            opsets.append({"domain": domain, "version": version})
        elif field == 25 and wire == 2:
            functions += 1
            if functions > budget.max_attributes:
                raise ProtobufParseError("onnx_function_limit_exceeded")
    if graph_payload is None:
        raise ProtobufParseError("onnx_graph_missing")
    nodes, initializers, inputs, outputs = _parse_graph(graph_payload, budget)
    fingerprint_body = {
        "ir_version": ir_version,
        "opsets": sorted(opsets, key=lambda item: (item["domain"], item["version"])),
        "operators": [
            {
                "path": item.path,
                "domain": item.domain,
                "operator": item.operator,
                "attributes_sha256": item.attributes_sha256,
                "has_subgraph": item.has_subgraph,
            }
            for item in sorted(nodes, key=lambda item: item.path)
        ],
        "initializers": [
            {
                "name": item.name,
                "dtype": item.dtype,
                "dimensions": list(item.dimensions),
                "external_data": [list(pair) for pair in item.external_data],
                "external_location": item.external_location,
                "raw_bytes": item.raw_bytes,
            }
            for item in sorted(initializers, key=lambda item: item.name)
        ],
        "inputs": [{"name": item.name, "dtype": item.dtype, "dimensions": list(item.dimensions)} for item in inputs],
        "outputs": [{"name": item.name, "dtype": item.dtype, "dimensions": list(item.dimensions)} for item in outputs],
        "function_count": functions,
    }
    return {
        "schema": "sentinel-edge-onnx-graph-fingerprint/1.0",
        "model_sha256": sha256_file(model_path),
        **fingerprint_body,
        "graph_capability_sha256": sha256_bytes(canonical_json_bytes(fingerprint_body)),
        "protobuf_fields_seen": budget.fields_seen,
    }


def inspect_onnx_graph_bounded(path: str | Path, *, timeout_seconds: float = 5.0) -> dict[str, Any]:
    """Inspect an untrusted model in a separate, time-bounded worker process."""
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    request = json.dumps({"path": str(Path(path).resolve())})
    child = (
        "import json,sys; from sentinel_edge.runtime.model_packages import inspect_onnx_graph; "
        "p=json.loads(sys.stdin.read()); print(json.dumps(inspect_onnx_graph(p['path']), sort_keys=True))"
    )
    python_args = [sys.executable, "-I", "-c", child] if os.name == "posix" else [sys.executable, "-c", child]
    project_root = Path(__file__).resolve().parents[3]
    popen_kwargs: dict[str, Any] = {
        "cwd": str(project_root),
        "env": {"PYTHONHASHSEED": "0", "PATH": os.environ.get("PATH", "")},
        "start_new_session": os.name == "posix",
        "close_fds": True,
    }
    if os.name == "posix":
        import resource

        def limit_worker() -> None:
            resource.setrlimit(resource.RLIMIT_CPU, (max(1, int(timeout_seconds) + 1), max(1, int(timeout_seconds) + 1)))
            resource.setrlimit(resource.RLIMIT_AS, (ONNX_WORKER_MAX_ADDRESS_SPACE_BYTES, ONNX_WORKER_MAX_ADDRESS_SPACE_BYTES))
            resource.setrlimit(resource.RLIMIT_NOFILE, (ONNX_WORKER_MAX_FILE_DESCRIPTORS, ONNX_WORKER_MAX_FILE_DESCRIPTORS))

        popen_kwargs["preexec_fn"] = limit_worker
    elif hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
        popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    try:
        result = subprocess.run(
            python_args, input=request, text=True,
            capture_output=True, timeout=timeout_seconds, check=False,
            **popen_kwargs,
        )
    except subprocess.TimeoutExpired as exc:
        raise ProtobufParseError("onnx_inspection_timeout") from exc
    if result.returncode != 0:
        raise ProtobufParseError("onnx_inspection_worker_failed")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ProtobufParseError("onnx_inspection_worker_invalid_output") from exc


def _safe_member(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    candidate.relative_to(root.resolve())
    return candidate


def _read_only(path: Path) -> bool:
    mode = stat.S_IMODE(path.stat().st_mode)
    return mode & 0o222 == 0


def _external_locations(graph: dict[str, Any]) -> tuple[str, ...]:
    locations: list[str] = []
    for item in graph["initializers"]:
        entries = dict(item["external_data"])
        location = entries.get("location")
        if item["external_location"] and not location:
            locations.append("")
        elif location is not None:
            locations.append(location)
    return tuple(locations)


def _validate_tensor_contracts(
    observed: list[dict[str, Any]], declared: tuple[TensorAllocationContract, ...], *, direction: str
) -> list[str]:
    failures: list[str] = []
    observed_by_name = {item["name"]: item for item in observed}
    declared_by_name = {item.name: item for item in declared}
    if set(observed_by_name) != set(declared_by_name):
        failures.append(f"{direction}_tensor_set_mismatch")
    for name, contract in declared_by_name.items():
        item = observed_by_name.get(name)
        if item is None:
            continue
        if item["dtype"] != contract.dtype:
            failures.append(f"{direction}_dtype_mismatch:{name}")
        dimensions = item["dimensions"]
        if len(dimensions) != contract.rank:
            failures.append(f"{direction}_rank_mismatch:{name}")
            continue
        for index, (observed_dimension, bound) in enumerate(zip(dimensions, contract.dimensions)):
            if isinstance(observed_dimension, int):
                if observed_dimension < bound.minimum or observed_dimension > bound.maximum:
                    failures.append(f"{direction}_dimension_out_of_bounds:{name}:{index}")
            elif isinstance(observed_dimension, str):
                if bound.symbol is not None and observed_dimension != bound.symbol:
                    failures.append(f"{direction}_symbol_mismatch:{name}:{index}")
                if bound.maximum <= 0:
                    failures.append(f"{direction}_unbounded_symbolic_dimension:{name}:{index}")
            else:
                failures.append(f"{direction}_unknown_dimension:{name}:{index}")
    return failures


def admit_model_package(
    manifest: ModelPackageManifest | dict[str, Any],
    *,
    root: str | Path,
    runtime: RuntimeAdmissionContext | dict[str, Any],
    runtime_issue_evaluation: dict[str, Any] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    package = manifest if isinstance(manifest, ModelPackageManifest) else ModelPackageManifest.model_validate(manifest)
    runtime_context = runtime if isinstance(runtime, RuntimeAdmissionContext) else RuntimeAdmissionContext.model_validate(runtime)
    repository_root = Path(root).resolve()
    failures: list[str] = []
    limitations: list[str] = []
    try:
        release_root = _safe_member(repository_root, package.release_root)
        model_path = _safe_member(release_root, package.model_path)
    except (ValueError, OSError):
        release_root = repository_root
        model_path = repository_root / "__invalid__"
        failures.append("model_path_outside_release_root")
    if not release_root.is_dir():
        failures.append("release_root_missing")
    elif not _read_only(release_root):
        failures.append("release_root_not_read_only")
    declared_files = {item.path: item for item in package.package_files}
    for relative, declared in declared_files.items():
        try:
            path = _safe_member(release_root, relative)
        except ValueError:
            failures.append(f"package_path_outside_root:{relative}")
            continue
        if not path.is_file():
            failures.append(f"package_file_missing:{relative}")
            continue
        if sha256_file(path) != declared.sha256:
            failures.append(f"package_file_digest_mismatch:{relative}")
        if path.stat().st_size != declared.bytes:
            failures.append(f"package_file_size_mismatch:{relative}")
        if not _read_only(path):
            failures.append(f"package_file_not_read_only:{relative}")
    if model_path.is_file() and sha256_file(model_path) != package.model_sha256:
        failures.append("model_digest_mismatch")
    graph: dict[str, Any] | None = None
    if model_path.is_file():
        try:
            graph = inspect_onnx_graph_bounded(model_path)
        except (OSError, ProtobufParseError, ValueError) as exc:
            failures.append(f"onnx_graph_invalid:{exc}")
    else:
        failures.append("model_artifact_missing")
    if graph is not None:
        imported = {item["domain"]: item["version"] for item in graph["opsets"]}
        for domain, version in imported.items():
            bounds = package.allowed_opsets.get(domain)
            if bounds is None or not bounds[0] <= version <= bounds[1]:
                failures.append(f"opset_not_allowed:{domain}:{version}")
        for operator in graph["operators"]:
            domain = operator["domain"]
            name = operator["operator"]
            if domain not in {"ai.onnx", "ai.onnx.ml"} and domain not in package.allowed_custom_domains:
                failures.append(f"custom_domain_not_allowed:{domain}")
            if name not in package.allowed_operators.get(domain, ()):
                failures.append(f"operator_not_allowed:{domain}:{name}")
            if operator["has_subgraph"] and not package.control_flow_allowed:
                failures.append(f"control_flow_not_allowed:{operator['path']}")
            if name.lower() in {"pyop", "pythonop"} or domain.lower().startswith("ai.onnx.contrib.python"):
                failures.append("python_operator_not_allowed")
        if graph["function_count"]:
            failures.append("local_functions_not_allowed")
        external_locations = _external_locations(graph)
        if external_locations and not package.external_data_allowed:
            failures.append("external_data_disabled")
        for location in external_locations:
            candidate = PurePosixPath(location)
            if not location or candidate.is_absolute() or ".." in candidate.parts or "://" in location:
                failures.append(f"external_data_path_unsafe:{location or '<missing>'}")
            if candidate.as_posix() not in package.allowed_external_data:
                failures.append(f"external_data_not_manifest_approved:{candidate.as_posix()}")
        failures.extend(_validate_tensor_contracts(graph["inputs"], package.inputs, direction="input"))
        failures.extend(_validate_tensor_contracts(graph["outputs"], package.outputs, direction="output"))
    if runtime_context.execution_provider != package.expected_execution_provider:
        failures.append("execution_provider_mismatch")
    if runtime_context.fallback_observed and not package.fallback_allowed:
        failures.append("provider_fallback_observed")
    if not runtime_context.provider_assignment_proven:
        failures.append("provider_assignment_not_proven")
    if runtime_issue_evaluation is None:
        failures.append("runtime_issue_evaluation_missing")
    elif runtime_issue_evaluation.get("activation_allowed") is not True:
        failures.append("runtime_issue_evaluation_failed")
    if now >= package.expires_at:
        failures.append("model_package_manifest_expired")
    if not runtime_context.target_host_qualified:
        limitations.append("target_host_not_qualified")
    if not runtime_context.target_runtime_measured:
        limitations.append("target_runtime_not_measured")
    target_qualified = not failures and runtime_context.target_host_qualified and runtime_context.target_runtime_measured
    release_admissible = target_qualified and bool(runtime_issue_evaluation and runtime_issue_evaluation.get("target_qualified") is True)
    provider_assignment = [
        {"path": item["path"], "operator": item["operator"], "provider": runtime_context.execution_provider}
        for item in (graph or {}).get("operators", [])
    ]
    if runtime_context.fallback_observed:
        for item in provider_assignment:
            item["fallback"] = True
    body = {
        "schema": "sentinel-edge-model-package-admission/1.0",
        "package_id": package.package_id,
        "manifest_sha256": sha256_bytes(canonical_json_bytes(package.model_dump(mode="json", by_alias=True))),
        "model_sha256": package.model_sha256,
        "graph_capability_sha256": graph.get("graph_capability_sha256") if graph else None,
        "runtime_package_sha256": runtime_context.runtime_package_sha256,
        "runtime_name": runtime_context.runtime_name,
        "runtime_version": runtime_context.runtime_version,
        "execution_provider": runtime_context.execution_provider,
        "provider_assignment": provider_assignment,
        "provider_fallback_observed": runtime_context.fallback_observed,
        "architecture": runtime_context.architecture,
        "input_allocation_bytes": sum(item.maximum_bytes for item in package.inputs),
        "output_allocation_bytes": sum(item.maximum_bytes for item in package.outputs),
        "graph": graph,
        "admission_passed": not failures,
        "target_qualified": target_qualified,
        "release_admissible": release_admissible,
        "failures": sorted(set(failures)),
        "limitations": sorted(set(limitations)),
        "evaluated_at": now.isoformat(),
    }
    return {**body, "report_digest": sha256_bytes(canonical_json_bytes(body))}


def scan_model_execution_boundaries(root: str | Path) -> dict[str, Any]:
    source_root = Path(root).resolve() / "src" / "sentinel_edge"
    forbidden_import_roots = {"onnxruntime", "tensorflow", "torch", "tflite_runtime", "openvino"}
    allowed_non_release_prefixes = {
        "sentinel_edge.qualification",
        "sentinel_edge.release",
        "sentinel_edge.benchmark",
        "sentinel_edge.runtime",
    }
    findings: list[dict[str, str]] = []
    files_scanned = 0
    for path in sorted(source_root.rglob("*.py")):
        files_scanned += 1
        module = ".".join(path.relative_to(source_root.parent).with_suffix("").parts)
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            findings.append({"path": str(path.relative_to(Path(root))), "kind": "syntax_error", "detail": str(exc)})
            continue
        for node in ast.walk(tree):
            imported: str | None = None
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported = alias.name.split(".")[0]
                    if imported in forbidden_import_roots and not any(module.startswith(prefix) for prefix in allowed_non_release_prefixes):
                        findings.append({"path": str(path.relative_to(Path(root))), "kind": "runtime_import_outside_component_3", "detail": alias.name})
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported = node.module.split(".")[0]
                if imported in forbidden_import_roots and not any(module.startswith(prefix) for prefix in allowed_non_release_prefixes):
                    findings.append({"path": str(path.relative_to(Path(root))), "kind": "runtime_import_outside_component_3", "detail": node.module})
    body = {
        "schema": "sentinel-edge-model-execution-boundary-scan/1.0",
        "files_scanned": files_scanned,
        "valid": not findings,
        "findings": findings,
        "allowed_non_release_tooling": sorted(allowed_non_release_prefixes - {"sentinel_edge.runtime"}),
        "release_execution_boundary": "sentinel_edge.runtime",
    }
    return {**body, "report_digest": sha256_bytes(canonical_json_bytes(body))}


def write_model_package_report(path: str | Path, report: dict[str, Any]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output
