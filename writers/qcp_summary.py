"""
Creates summary of results for qcp pairwise comparison (both per circuit and overall)
Records num_calls, num_success, num_failed, success_rate, total_time, avg_time, min_time, max_time, max_qubits, errors, circuit-specific property pass/fail rates
"""

import json
from pathlib import Path
from typing import Any, Dict, List


_PREFIX = "time_evaluator_"
_PROP_PREFIX = "prop_"


def _parse_time_key(key: str):
    if not key.startswith(_PREFIX):
        return None
    rest = key[len(_PREFIX):]
    idx_str, _, eid = rest.partition("_")
    if not idx_str.isdigit():
        return None
    return idx_str, eid


def _collect_entries(rows: List[Dict[str, Any]]):
    for row in rows:
        for k, v in row.items():
            parsed = _parse_time_key(k)
            if parsed is None:
                continue
            idx_str, eid = parsed
            yield eid, {
                "time": v,
                "success": bool(row.get(f"success_evaluator_{idx_str}_{eid}", False)),
                "num_qubits": int(row.get(f"num_qubits_evaluator_{idx_str}_{eid}", 0) or 0),
                "error": row.get(f"error_evaluator_{idx_str}_{eid}"),
            }


def _collect_property_entries(rows):
    for row in rows:
        for k, v in row.items():
            if not k.startswith(_PROP_PREFIX) or "_evaluator_" not in k:
                continue
            rest = k[len(_PROP_PREFIX):]
            prop_name, _, tail = rest.partition("_evaluator_")
            idx_str, _, eid = tail.partition("_")
            if not idx_str.isdigit():
                continue
            yield eid, prop_name, bool(v)


def _aggregate_properties(rows):
    agg: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for eid, prop_name, passed in _collect_property_entries(rows):
        bucket = agg.setdefault(prop_name, {}).setdefault(
            eid, {"passed": 0, "total": 0}
        )
        bucket["total"] += 1
        if passed:
            bucket["passed"] += 1
    for prop_name, per_eval in agg.items():
        for eid, s in per_eval.items():
            s["rate"] = s["passed"] / s["total"] if s["total"] else 0.0
            if s["passed"] == s["total"] and s["total"] > 0:
                s["status"] = "PASS"
            elif s["passed"] == 0:
                s["status"] = "FAIL"
            else:
                s["status"] = "PARTIAL"
    return agg


def aggregate(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not entries:
        return {
            "num_calls": 0,
            "num_success": 0,
            "num_failed": 0,
            "success_rate": 0.0,
            "total_time": 0.0,
            "avg_time": 0.0,
            "min_time": 0.0,
            "max_time": 0.0,
            "max_qubits": 0,
            "errors": {},
        }
    times = [e["time"] for e in entries]
    successes = [e["success"] for e in entries]
    qs = [e["num_qubits"] for e in entries if e["num_qubits"]]
    errors: Dict[str, int] = {}
    for e in entries:
        if e.get("error"):
            errors[e["error"]] = errors.get(e["error"], 0) + 1
    return {
        "num_calls": len(entries),
        "num_success": sum(successes),
        "num_failed": len(entries) - sum(successes),
        "success_rate": sum(successes) / len(entries),
        "total_time": sum(times),
        "avg_time": sum(times) / len(times),
        "min_time": min(times),
        "max_time": max(times),
        "max_qubits": max(qs) if qs else 0,
        "errors": errors,
    }


def compute_circuit_summary(circuit_id: str, rows: List[Dict[str, Any]],
                            benchmark_id: str, run_id: str) -> Dict[str, Any]:
    by_eval: Dict[str, List[Dict[str, Any]]] = {}
    for eid, entry in _collect_entries(rows):
        by_eval.setdefault(eid, []).append(entry)
    return {
        "benchmark": benchmark_id,
        "run_id": run_id,
        "circuit_id": circuit_id,
        "num_inputs": len(rows),
        "evaluators": {eid: aggregate(entries) for eid, entries in by_eval.items()},
        "properties": _aggregate_properties(rows),
    }


def compute_run_summary(accumulated: Dict[str, List[Dict[str, Any]]], benchmark_id: str, run_id: str, elapsed_seconds: float) -> Dict[str, Any]:
    per_circuit: Dict[str, Any] = {}
    global_by_eval: Dict[str, List[Dict[str, Any]]] = {}
    for cid, rows in accumulated.items():
        circ_by_eval: Dict[str, List[Dict[str, Any]]] = {}
        for eid, entry in _collect_entries(rows):
            circ_by_eval.setdefault(eid, []).append(entry)
            global_by_eval.setdefault(eid, []).append(entry)
        per_circuit[cid] = {
            "num_inputs": len(rows),
            **{eid: aggregate(entries) for eid, entries in circ_by_eval.items()},
        }

    all_prop_by_eval: Dict[str, Dict[str, Dict[str, int]]] = {}
    for cid, rows in accumulated.items():
        per_circuit_props = _aggregate_properties(rows)
        for prop_name, per_eval in per_circuit_props.items():
            bucket = all_prop_by_eval.setdefault(prop_name, {})
            for eid, s in per_eval.items():
                b = bucket.setdefault(eid, {"passed": 0, "total": 0})
                b["passed"] += s["passed"]
                b["total"] += s["total"]
    for prop_name, per_eval in all_prop_by_eval.items():
        for eid, s in per_eval.items():
            s["rate"] = s["passed"] / s["total"] if s["total"] else 0.0
            if s["passed"] == s["total"] and s["total"] > 0:
                s["status"] = "PASS"
            elif s["passed"] == 0:
                s["status"] = "FAIL"
            else:
                s["status"] = "PARTIAL"

    return {
        "benchmark": benchmark_id,
        "run_id": run_id,
        "circuits_processed": len(accumulated),
        "elapsed_seconds": elapsed_seconds,
        "circuits": per_circuit,
        "evaluators": {eid: aggregate(entries) for eid, entries in global_by_eval.items()},
        "properties": all_prop_by_eval,
    }


def write_circuit_summary(run_path: str, circuit_id: str, summary: Dict[str, Any]) -> str:
    out_dir = Path(run_path) / circuit_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "qcp_summary.json"
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    return str(out_path)


def write_run_summary(run_path: str, summary: Dict[str, Any]) -> str:
    out_path = Path(run_path) / "qcp_summary.json"
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    return str(out_path)


def format_compact_line(circuit_id: str, circuit_summary: Dict[str, Any], circuits_done: int, circuits_total: int, elapsed_seconds: float) -> str:
    mins, secs = divmod(int(elapsed_seconds), 60)
    hrs, mins = divmod(mins, 60)
    elapsed = f"{hrs:02d}:{mins:02d}:{secs:02d}"
    parts = []
    for eid, s in circuit_summary.get("evaluators", {}).items():
        if s["num_calls"] == 0:
            continue
        parts.append(
            f"{eid} ok={s['num_success']}/{s['num_calls']} "
            f"avg={s['avg_time']:.3f}s "
            f"tot={s['total_time']:.3f}s "
            f"qmax={s['max_qubits']}"
        )

    props = circuit_summary.get("properties", {})
    if props:
        shared = [
            k for k, v in props.items()
            if all(s.get("status") == "PASS" for s in v.values())
        ]
        parts.append(f"props_pass={len(shared)}/{len(props)}")

    joined = " | ".join(parts) if parts else "no evaluator results"
    return (f"[{circuits_done}/{circuits_total}] {circuit_id} | "
            f"{joined} | elapsed {elapsed}")