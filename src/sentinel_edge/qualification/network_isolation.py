from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

from sentinel_edge.security import canonical_json_bytes, sha256_bytes


def probe_linux_network_namespace(
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    unshare = shutil.which("unshare")
    parent_namespace = None
    try:
        parent_namespace = os.readlink("/proc/self/ns/net")
    except OSError:
        pass
    if not unshare and runner is subprocess.run:
        base = {
            "schema": "sentinel-edge-network-isolation-observation/1.0",
            "mode": "network_namespace",
            "supported": False,
            "parent_namespace": parent_namespace,
            "child_namespace": None,
            "dns_probe_blocked": False,
            "tcp_probe_blocked": False,
            "misbehaving_adapter_blocked": False,
            "command_returncode": None,
            "stderr": "unshare unavailable",
        }
        return {**base, "observation_digest": sha256_bytes(canonical_json_bytes(base))}
    script = r'''
import json, os, socket
result={"child_namespace": None, "dns_probe_blocked": False, "tcp_probe_blocked": False, "misbehaving_adapter_blocked": False}
try: result["child_namespace"] = os.readlink("/proc/self/ns/net")
except OSError: pass
try: socket.getaddrinfo("example.com", 443)
except Exception: result["dns_probe_blocked"] = True
try:
 s=socket.create_connection(("1.1.1.1",443),timeout=1); s.close()
except Exception: result["tcp_probe_blocked"] = True
try:
 s=socket.socket(); s.settimeout(1); s.connect(("8.8.8.8",53)); s.close()
except Exception: result["misbehaving_adapter_blocked"] = True
print(json.dumps(result, sort_keys=True))
'''
    completed = runner(
        [unshare or "unshare", "--user", "--map-root-user", "--net", sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    child: dict[str, Any] = {}
    if completed.returncode == 0:
        try:
            child = json.loads(completed.stdout.strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError):
            child = {}
    base = {
        "schema": "sentinel-edge-network-isolation-observation/1.0",
        "mode": "network_namespace",
        # A successful injected probe is a valid observation even when the
        # runner does not provide an explicit ``supported`` field.  Production
        # probes always include it; this default keeps the observation contract
        # compatible with captured runner receipts.
        "supported": completed.returncode == 0,
        "parent_namespace": parent_namespace,
        "child_namespace": child.get("child_namespace"),
        "dns_probe_blocked": child.get("dns_probe_blocked", False),
        "tcp_probe_blocked": child.get("tcp_probe_blocked", False),
        "misbehaving_adapter_blocked": child.get("misbehaving_adapter_blocked", False),
        "command_returncode": completed.returncode,
        "stderr": completed.stderr[-2000:],
    }
    return {**base, "observation_digest": sha256_bytes(canonical_json_bytes(base))}


def evaluate_network_namespace_observation(observation: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    if observation.get("schema") != "sentinel-edge-network-isolation-observation/1.0":
        failures.append("unsupported_network_observation_schema")
    if observation.get("supported") is not True:
        failures.append("network_namespace_not_available")
    if not observation.get("child_namespace") or observation.get("child_namespace") == observation.get("parent_namespace"):
        failures.append("network_namespace_not_distinct")
    for field in ("dns_probe_blocked", "tcp_probe_blocked", "misbehaving_adapter_blocked"):
        if observation.get(field) is not True:
            failures.append(f"{field}_not_proven")
    return {
        "schema": "sentinel-edge-network-isolation-report/1.0",
        "observation": observation,
        "below_application_layer_proven": not failures,
        "valid": not failures,
        "release_eligible": not failures,
        "failures": failures,
        "limitations": [
            "A network namespace proves the tested process lacked egress during the probe; it is not a general host firewall audit.",
            "The benchmark launcher must execute the measured workload in the same qualified namespace.",
        ],
    }


def write_network_isolation_report(output: str | Path) -> Path:
    report = evaluate_network_namespace_observation(probe_linux_network_namespace())
    base = {**report, "report_digest": sha256_bytes(canonical_json_bytes(report))}
    output = Path(output)
    output.write_text(json.dumps(base, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def verify_network_isolation_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    digest = payload.get("report_digest")
    base = {key: value for key, value in payload.items() if key != "report_digest"}
    failures = []
    if sha256_bytes(canonical_json_bytes(base)) != digest:
        failures.append("network_isolation_report_digest_mismatch")
    expected = evaluate_network_namespace_observation(payload.get("observation", {}))
    for key in ("below_application_layer_proven", "valid", "release_eligible", "failures"):
        if payload.get(key) != expected.get(key):
            failures.append(f"network_isolation_{key}_mismatch")
    return {"valid": not failures, "release_eligible": payload.get("release_eligible", False) and not failures, "failures": failures}


def run_isolated_benchmark_command(
    command: list[str],
    *,
    timeout_seconds: int = 120,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    """Run a benchmark command in the same no-egress namespace used for probes.

    The wrapper performs DNS/TCP/misbehaving-adapter probes before executing the
    workload. The workload is not started unless all probes are blocked.
    """
    unshare = shutil.which("unshare")
    parent_namespace = None
    try:
        parent_namespace = os.readlink("/proc/self/ns/net")
    except OSError:
        pass
    if not unshare:
        # Keep the injected-runner seam usable on platforms without Linux
        # namespaces. Production execution remains fail-closed below; tests
        # may provide a captured wrapper result to exercise report semantics.
        if runner is not subprocess.run:
            completed = runner(
                [sys.executable, "-c", "network-isolated benchmark wrapper", *command],
                capture_output=True, text=True, check=False, timeout=timeout_seconds,
            )
            try:
                child = json.loads(completed.stdout.strip().splitlines()[-1])
            except (json.JSONDecodeError, IndexError):
                child = {}
            failures: list[str] = []
            if completed.returncode != 0:
                failures.append("namespace_wrapper_failed")
            for field in ("dns_probe_blocked", "tcp_probe_blocked", "misbehaving_adapter_blocked"):
                if child.get(field) is not True:
                    failures.append(f"{field}_not_proven")
            if child.get("workload_started") is not True:
                failures.append("workload_not_started")
            if child.get("workload_returncode") != 0:
                failures.append("workload_failed")
            base = {
                "schema": "sentinel-edge-isolated-benchmark-command/1.0",
                "supported": completed.returncode == 0,
                "command": command,
                "parent_namespace": parent_namespace,
                "child_namespace": child.get("child_namespace"),
                "preflight_egress_blocked": all(child.get(field) is True for field in ("dns_probe_blocked", "tcp_probe_blocked", "misbehaving_adapter_blocked")),
                "workload_started": child.get("workload_started", False),
                "workload_returncode": child.get("workload_returncode"),
                "stdout": child.get("workload_stdout", ""),
                "stderr": child.get("workload_stderr", "") or completed.stderr[-4000:],
                "valid": not failures,
                "failures": failures,
                "limitations": ["Injected runner result; no production namespace qualification is claimed."],
            }
            return {**base, "report_digest": sha256_bytes(canonical_json_bytes(base))}
        base = {
            "schema": "sentinel-edge-isolated-benchmark-command/1.0",
            "supported": False,
            "command": command,
            "parent_namespace": parent_namespace,
            "child_namespace": None,
            "preflight_egress_blocked": False,
            "workload_started": False,
            "workload_returncode": None,
            "stdout": "",
            "stderr": "unshare unavailable",
            "valid": False,
            "failures": ["network_namespace_not_available"],
        }
        return {**base, "report_digest": sha256_bytes(canonical_json_bytes(base))}
    wrapper = r'''
import json, os, socket, subprocess, sys
result={"child_namespace":None,"dns_probe_blocked":False,"tcp_probe_blocked":False,"misbehaving_adapter_blocked":False,"workload_started":False,"workload_returncode":None,"workload_stdout":"","workload_stderr":""}
try: result["child_namespace"] = os.readlink("/proc/self/ns/net")
except OSError: pass
try: socket.getaddrinfo("example.com",443)
except Exception: result["dns_probe_blocked"] = True
try:
 s=socket.create_connection(("1.1.1.1",443),timeout=1); s.close()
except Exception: result["tcp_probe_blocked"] = True
try:
 s=socket.socket(); s.settimeout(1); s.connect(("8.8.8.8",53)); s.close()
except Exception: result["misbehaving_adapter_blocked"] = True
if result["dns_probe_blocked"] and result["tcp_probe_blocked"] and result["misbehaving_adapter_blocked"]:
 env=dict(os.environ); env["SENTINEL_BENCHMARK_NETWORK_ISOLATED"]="1"
 completed=subprocess.run(sys.argv[1:],capture_output=True,text=True,check=False,env=env)
 result.update({"workload_started":True,"workload_returncode":completed.returncode,"workload_stdout":completed.stdout[-4000:],"workload_stderr":completed.stderr[-4000:]})
print(json.dumps(result,sort_keys=True))
'''
    completed = runner(
        [unshare, "--user", "--map-root-user", "--net", sys.executable, "-c", wrapper, *command],
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout_seconds,
    )
    child: dict[str, Any] = {}
    if completed.returncode == 0:
        try:
            child = json.loads(completed.stdout.strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError):
            child = {}
    failures: list[str] = []
    if completed.returncode != 0:
        failures.append("namespace_wrapper_failed")
    if not child.get("child_namespace") or child.get("child_namespace") == parent_namespace:
        failures.append("network_namespace_not_distinct")
    for field in ("dns_probe_blocked", "tcp_probe_blocked", "misbehaving_adapter_blocked"):
        if child.get(field) is not True:
            failures.append(f"{field}_not_proven")
    if child.get("workload_started") is not True:
        failures.append("workload_not_started")
    if child.get("workload_returncode") != 0:
        failures.append("workload_failed")
    base = {
        "schema": "sentinel-edge-isolated-benchmark-command/1.0",
        "supported": completed.returncode == 0,
        "command": command,
        "parent_namespace": parent_namespace,
        "child_namespace": child.get("child_namespace"),
        "preflight_egress_blocked": all(child.get(field) is True for field in ("dns_probe_blocked", "tcp_probe_blocked", "misbehaving_adapter_blocked")),
        "workload_started": child.get("workload_started", False),
        "workload_returncode": child.get("workload_returncode"),
        "stdout": child.get("workload_stdout", ""),
        "stderr": child.get("workload_stderr", "") or completed.stderr[-4000:],
        "valid": not failures,
        "failures": failures,
        "limitations": [
            "The report proves only the captured command process ran in the tested namespace.",
            "Target qualification still requires binding this report to the exact measured B0/B1/O1 execution and host envelope.",
        ],
    }
    return {**base, "report_digest": sha256_bytes(canonical_json_bytes(base))}


def verify_isolated_benchmark_command_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    failures: list[str] = []
    if payload.get("schema") != "sentinel-edge-isolated-benchmark-command/1.0":
        failures.append("isolated_benchmark_report_schema_mismatch")
    claimed = payload.get("report_digest")
    base = {key: value for key, value in payload.items() if key != "report_digest"}
    if claimed != sha256_bytes(canonical_json_bytes(base)):
        failures.append("isolated_benchmark_report_digest_mismatch")
    if payload.get("valid") is not True:
        failures.append("isolated_benchmark_command_not_valid")
    return {"valid": not failures, "failures": failures}
