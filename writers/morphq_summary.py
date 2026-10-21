import json
from pathlib import Path
from typing import Any, Dict, List, Optional

def _row_total_s(row: Dict[str, Any]) -> Optional[float]:
    if isinstance(row.get("total_s"), (int, float)):
        return float(row["total_s"])
    parts = [
        row.get("transform_s"),
        row.get("simulation_s"),
        row.get("comparison_s"),
    ]
    if all(isinstance(p, (int, float)) for p in parts):
        return sum(parts)
    return None

def _aggregate(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    n = len(rows)
    statuses = [str(r.get("status", "")) for r in rows]
    counts = {s: statuses.count(s) for s in set(statuses)}
    totals = [t for r in rows if (t := _row_total_s(r)) is not None]
    sims = [
        r["simulation_s"]
        for r in rows
        if isinstance(r.get("simulation_s"), (int, float))
    ]
    statistics = [
        r["statistic"]
        for r in rows
        if isinstance(r.get("statistic"), (int, float))
    ]
    pvals = [
        r["p_value"]
        for r in rows
        if isinstance(r.get("p_value"), (int, float))
    ]
    return {
        "num_calls": n,
        "num_match": counts.get("MATCH", 0),
        "num_mismatch": counts.get("MISMATCH", 0),
        "num_diverged": counts.get("DIVERGED", 0),
        "num_error": counts.get("ERROR", 0)
        + counts.get("REFERENCE_ERROR", 0),
        "num_skipped": counts.get("SKIPPED", 0),
        "status_counts": counts,
        "success_rate": (
            (counts.get("MATCH", 0) + counts.get("DIVERGED", 0)) / n
            if n else 0.0
        ),
        "total_s": sum(totals) if totals else None,
        "avg_s": (sum(totals) / len(totals)) if totals else None,
        "max_s": max(totals) if totals else None,
        "total_simulation_s": sum(sims) if sims else None,
        "avg_statistic": (
            sum(statistics) / len(statistics) if statistics else None
        ),
        "avg_p_value": (sum(pvals) / len(pvals)) if pvals else None,
    }


def _group_by_evaluator(
    rows: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row.get("evaluator", "?"), []).append(row)
    return grouped

def compute_circuit_summary(
    circuit_id: str,
    rows: List[Dict[str, Any]],
    benchmark_id: str,
    run_id: str,
) -> Dict[str, Any]:
    return {
        "benchmark": benchmark_id,
        "run_id": run_id,
        "circuit_id": circuit_id,
        "num_inputs": len({r.get("input_index") for r in rows}),
        "num_qubits": rows[0].get("num_qubits") if rows else None,
        "evaluators": {
            ev: _aggregate(ev_rows)
            for ev, ev_rows in _group_by_evaluator(rows).items()
        },
    }

def compute_run_summary(
    accumulated: Dict[str, List[Dict[str, Any]]],
    benchmark_id: str,
    run_id: str,
    elapsed_seconds: float,
) -> Dict[str, Any]:
    per_circuit: Dict[str, Any] = {}
    all_rows: List[Dict[str, Any]] = []
    for cid, rows in accumulated.items():
        per_circuit[cid] = compute_circuit_summary(
            cid, rows, benchmark_id, run_id
        )
        all_rows.extend(rows)
    return {
        "benchmark": benchmark_id,
        "run_id": run_id,
        "circuits_processed": len(accumulated),
        "elapsed_seconds": elapsed_seconds,
        "circuits": per_circuit,
        "evaluators": {
            ev: _aggregate(ev_rows)
            for ev, ev_rows in _group_by_evaluator(all_rows).items()
        },
    }


def write_circuit_summary(
    run_path: str, circuit_id: str, summary: Dict[str, Any]
) -> str:
    out_dir = Path(run_path) / circuit_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "summary.json"
    out.write_text(json.dumps(summary, indent=2, default=str) + "\n")
    return str(out)

def write_run_summary(run_path: str, summary: Dict[str, Any]) -> str:
    out = Path(run_path) / "summary.json"
    out.write_text(json.dumps(summary, indent=2, default=str) + "\n")
    return str(out)