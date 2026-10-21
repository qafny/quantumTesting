"""
Runner for QET vs MorphQ optimisation step comparison.
"""

import argparse
import csv
import datetime
import json
import logging
from pathlib import Path
from time import perf_counter
from typing import Any, Dict, List, Optional
from globals import TagProcessor
from readers.benchmarks import (
    LibraryQiskitBenchmark,
    CustomQiskitBenchmark,
)
from comparators.optimization_passes import OptimizationPassComparator
from comparators.morphq_opt import MorphQOptimisationPassComparator
from evaluators.passes import (
    Optimize1qGatesEvaluator,
    Optimize1qGatesDecompositionEvaluator,
    Optimize1qGatesSimpleCommutationEvaluator,
    CommutativeInverseCancellationEvaluator,
    OptimizeCliffordsEvaluator,
    OptimizeCliffordTEvaluator,
    Split2QUnitariesEvaluator,
    CommutativeOptimizationEvaluator,
    TwoQubitPeepholeEvaluator,
)
from writers import morphq_summary

OPTIMIZATION_PASS_EVALUATORS = [
    Optimize1qGatesEvaluator,
    Optimize1qGatesDecompositionEvaluator,
    Optimize1qGatesSimpleCommutationEvaluator,
    CommutativeInverseCancellationEvaluator,
    OptimizeCliffordsEvaluator,
    OptimizeCliffordTEvaluator,
    Split2QUnitariesEvaluator,
    CommutativeOptimizationEvaluator,
    TwoQubitPeepholeEvaluator,
]

def _safe_add(*values: Any) -> Any:
    total, any_val = 0.0, False
    for v in values:
        if isinstance(v, (int, float)):
            total += v
            any_val = True
    return total if any_val else ""


def _qet_row_total_s(row: Dict[str, Any]) -> Any:
    return _safe_add(
        row.get("transform_s"),
        row.get("simulation_s"),
        row.get("comparison_s"),
    )


def _write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.touch()
        return
    fields: List[str] = []
    seen = set()
    for row in rows:
        for k in row:
            if k not in seen:
                seen.add(k)
                fields.append(k)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=fields, extrasaction="ignore", restval=""
        )
        writer.writeheader()
        writer.writerows(rows)


def _join_rows_by_key(
    qet_rows: List[Dict[str, Any]],
    mq_rows: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    qet_by = {(r.get("evaluator"), r.get("input_index")): r for r in qet_rows}
    mq_by = {(r.get("evaluator"), r.get("input_index")): r for r in mq_rows}
    keys = sorted(
        set(qet_by) | set(mq_by), key=lambda k: (str(k[0]), k[1] or 0)
    )
    combined: List[Dict[str, Any]] = []
    for key in keys:
        q = qet_by.get(key, {})
        m = mq_by.get(key, {})
        combined.append(
            {
                "evaluator": key[0],
                "input_index": key[1],
                "circuit_id": q.get("circuit_id", m.get("circuit_id", "")),
                "num_qubits": q.get("num_qubits", m.get("num_qubits")),
                "qet_status": q.get("status", ""),
                "qet_passed": q.get("passed", ""),
                "qet_transform_s": q.get("transform_s", ""),
                "qet_simulation_s": q.get("simulation_s", ""),
                "qet_comparison_s": q.get("comparison_s", ""),
                "qet_total_s": _qet_row_total_s(q) if q else "",
                "morphq_status": m.get("status", ""),
                "morphq_statistic": m.get("statistic", ""),
                "morphq_p_value": m.get("p_value", ""),
                "morphq_transform_s": m.get("transform_s", ""),
                "morphq_simulation_s": m.get("simulation_s", ""),
                "morphq_comparison_s": m.get("comparison_s", ""),
                "morphq_total_s": m.get("total_s", ""),
            }
        )
    return combined


def _write_combined_summary(
    path: Path, qet_summary: Dict[str, Any], morphq_summary: Dict[str, Any]
) -> None:
    evaluators = (
        set(qet_summary.get("evaluators", {}))
        | set(morphq_summary.get("evaluators", {}))
    )
    rows: List[Dict[str, Any]] = []
    for ev in sorted(evaluators):
        q = qet_summary.get("evaluators", {}).get(ev, {})
        m = morphq_summary.get("evaluators", {}).get(ev, {})
        rows.append(
            {
                "evaluator": ev,
                "qet_num_calls": q.get("num_calls", 0),
                "qet_num_match": q.get("num_match", 0),
                "qet_num_mismatch": q.get("num_mismatch", 0),
                "qet_num_error": q.get("num_error", 0),
                "qet_total_s": q.get("total_s", ""),
                "qet_avg_s": q.get("avg_s", ""),
                "morphq_num_calls": m.get("num_calls", 0),
                "morphq_num_match": m.get("num_match", 0),
                "morphq_num_diverged": m.get("num_diverged", 0),
                "morphq_num_error": m.get("num_error", 0),
                "morphq_num_skipped": m.get("num_skipped", 0),
                "morphq_total_s": m.get("total_s", ""),
                "morphq_avg_s": m.get("avg_s", ""),
            }
        )
    _write_csv(path, rows)


def _write_scalability(
    path: Path,
    qet_by_circuit: Dict[str, List[Dict[str, Any]]],
    mq_by_circuit: Dict[str, List[Dict[str, Any]]],
) -> None:
    rows: List[Dict[str, Any]] = []
    for cid, q_rows in qet_by_circuit.items():
        q_by_ev: Dict[str, List[Dict[str, Any]]] = {}
        for r in q_rows:
            q_by_ev.setdefault(r.get("evaluator"), []).append(r)
        m_by_ev: Dict[str, List[Dict[str, Any]]] = {}
        for r in mq_by_circuit.get(cid, []):
            m_by_ev.setdefault(r.get("evaluator"), []).append(r)
        for ev in sorted(set(q_by_ev) | set(m_by_ev)):
            q_rows_ev = q_by_ev.get(ev, [])
            m_rows_ev = m_by_ev.get(ev, [])
            q_num_qubits = (
                q_rows_ev[0].get("num_qubits") if q_rows_ev else
                (m_rows_ev[0].get("num_qubits") if m_rows_ev else "")
            )
            q_totals = [
                _qet_row_total_s(r)
                for r in q_rows_ev
                if isinstance(_qet_row_total_s(r), (int, float))
            ]
            m_totals = [
                r["total_s"]
                for r in m_rows_ev
                if isinstance(r.get("total_s"), (int, float))
            ]
            q_statuses = [r.get("status", "") for r in q_rows_ev]
            m_statuses = [r.get("status", "") for r in m_rows_ev]
            rows.append(
                {
                    "circuit_id": cid,
                    "evaluator": ev,
                    "num_qubits": q_num_qubits,
                    "qet_statuses": "|".join(sorted(set(q_statuses))),
                    "qet_avg_s": (sum(q_totals) / len(q_totals)) if q_totals else "",
                    "qet_max_s": max(q_totals) if q_totals else "",
                    "morphq_statuses": "|".join(sorted(set(m_statuses))),
                    "morphq_avg_s": (sum(m_totals) / len(m_totals)) if m_totals else "",
                    "morphq_max_s": max(m_totals) if m_totals else "",
                    "morphq_skipped": "SKIPPED" in m_statuses,
                }
            )
    _write_csv(path, rows)


def _qiskit_version() -> str:
    try:
        import qiskit
        return qiskit.__version__
    except Exception:
        return ""

def run_compare(
    run_id: str,
    tags: List[str],
    base_out_dir: str,
    benchmark_path: str,
    shots: int,
    alpha: float,
    max_qubits: int,
    circuit_ids: Optional[List[str]] = None,
    max_inputs: Optional[int] = None,
) -> Path:
    if any(t in tags for t in ("parse_rph", "parse_rsh", "parse_rm")):
        raise ValueError(
            "Do not remove program operations in optimisation-pass tests"
        )
    TagProcessor().set_tags(tags=tags)

    if LibraryQiskitBenchmark.is_library_benchmark(benchmark_path):
        benchmark = LibraryQiskitBenchmark(benchmark_path)
    elif CustomQiskitBenchmark.is_custom_benchmark(benchmark_path):
        benchmark = CustomQiskitBenchmark(benchmark_path)
    else:
        raise ValueError(f"Unsupported benchmark: {benchmark_path}")

    run_path = Path(base_out_dir) / run_id
    run_path.mkdir(parents=True, exist_ok=True)
    benchmark_id = Path(benchmark_path).name
    started = perf_counter()

    (run_path / "run_metadata.json").write_text(
        json.dumps(
            {
                "qiskit_version": _qiskit_version(),
                "benchmark_path": str(benchmark_path),
                "mode": "qet_vs_morphq_optimisation_passes",
                "shots": shots,
                "alpha": alpha,
                "max_qubits": max_qubits,
                "evaluators": [c.get_identifier() for c in OPTIMIZATION_PASS_EVALUATORS],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    qet_by_circuit: Dict[str, List[Dict[str, Any]]] = {}
    mq_by_circuit: Dict[str, List[Dict[str, Any]]] = {}

    if circuit_ids:
        wanted = set(circuit_ids)
        unknown = wanted - set(benchmark.config["circuits"])
        if unknown:
            raise ValueError(
                f"Unknown circuit_id(s) for benchmark {benchmark_id!r}: "
                f"{sorted(unknown)}. "
                f"Available: {sorted(benchmark.config['circuits'])}"
            )
        logging.info(
            "Filtering to %d circuit(s): %s",
            len(wanted), sorted(wanted),
        )

    for circuit_id, info in benchmark.config["circuits"].items():
        if circuit_ids and circuit_id not in circuit_ids:
            continue
        logging.info("Processing circuit: %s", circuit_id)
        generation = info.get("generation", {})
        extra = {
            "circuit_id": circuit_id,
            "family": generation.get("family", ""),
            "circuit_seed": generation.get("circuit_seed", ""),
            "input_seed": generation.get("input_seed", ""),
            "target_patterns": generation.get("target_patterns", ""),
        }

        try:
            circuit = benchmark.get_circuit_from_info(info)
            inputs = benchmark.get_inputs_from_info(info)
            extra["inputs_count"] = len(inputs)
            if max_inputs is not None and max_inputs > 0:
                inputs = inputs[:max_inputs]
                extra["inputs_count"] = len(inputs)
        except Exception as exc:
            logging.exception("Failed to load circuit %s", circuit_id)
            error = f"{type(exc).__name__}: {exc}"
            qet_by_circuit[circuit_id] = [
                {"circuit_id": circuit_id, "evaluator": "qet",
                 "status": "ERROR", "error": error}
            ]
            mq_by_circuit[circuit_id] = [
                {"circuit_id": circuit_id, "evaluator": "morphq",
                 "status": "ERROR", "error": error}
            ]
            continue

        try:
            qet_comparator = OptimizationPassComparator(
                circuit=circuit,
                evaluator_classes=OPTIMIZATION_PASS_EVALUATORS,
                inputs=inputs,
            )
            qet_rows = qet_comparator.compare()
            for r in qet_rows:
                r.update(extra)
        except Exception as exc:
            logging.exception("QET pass comparison failed for %s", circuit_id)
            qet_rows = [{
                "circuit_id": circuit_id, "evaluator": "qet",
                "status": "ERROR", "error": f"{type(exc).__name__}: {exc}",
            }]

        try:
            mq_comparator = MorphQOptimisationPassComparator(
                circuit=circuit,
                evaluator_classes=OPTIMIZATION_PASS_EVALUATORS,
                inputs=inputs,
                shots=shots,
                alpha=alpha,
                max_qubits=max_qubits,
            )
            mq_rows = mq_comparator.compare()
            for r in mq_rows:
                r.update(extra)
        except Exception as exc:
            logging.exception("MorphQ pass comparison failed for %s", circuit_id)
            mq_rows = [{
                "circuit_id": circuit_id, "evaluator": "morphq",
                "status": "ERROR", "error": f"{type(exc).__name__}: {exc}",
            }]

        qet_by_circuit[circuit_id] = qet_rows
        mq_by_circuit[circuit_id] = mq_rows

        circuit_dir = run_path / circuit_id
        circuit_dir.mkdir(parents=True, exist_ok=True)
        _write_csv(circuit_dir / "qet_results.csv", qet_rows)
        _write_csv(circuit_dir / "morphq_results.csv", mq_rows)
        _write_csv(
            circuit_dir / "comparison.csv",
            _join_rows_by_key(qet_rows, mq_rows),
        )
        (circuit_dir / "qet_summary.json").write_text(
            json.dumps(
                morphq_summary.compute_circuit_summary(
                    circuit_id, qet_rows, benchmark_id, run_id
                ),
                indent=2,
                default=str,
            )
            + "\n"
        )
        (circuit_dir / "morphq_summary.json").write_text(
            json.dumps(
                morphq_summary.compute_circuit_summary(
                    circuit_id, mq_rows, benchmark_id, run_id
                ),
                indent=2,
                default=str,
            )
            + "\n"
        )

        _write_csv(
            run_path / "qet_all_rows.csv",
            [r for rows in qet_by_circuit.values() for r in rows],
        )
        _write_csv(
            run_path / "morphq_all_rows.csv",
            [r for rows in mq_by_circuit.values() for r in rows],
        )
        _write_csv(
            run_path / "comparison.csv",
            [
                r
                for cid, q_rows in qet_by_circuit.items()
                for r in _join_rows_by_key(
                    q_rows, mq_by_circuit.get(cid, [])
                )
            ],
        )

        elapsed = perf_counter() - started
        qet_summary = morphq_summary.compute_run_summary(
            qet_by_circuit, benchmark_id, run_id, elapsed
        )
        mq_run_summary = morphq_summary.compute_run_summary(
            mq_by_circuit, benchmark_id, run_id, elapsed
        )
        (run_path / "qet_summary.json").write_text(
            json.dumps(qet_summary, indent=2, default=str) + "\n"
        )
        (run_path / "morphq_summary.json").write_text(
            json.dumps(mq_run_summary, indent=2, default=str) + "\n"
        )
        _write_combined_summary(
            run_path / "combined_summary.csv", qet_summary, mq_run_summary
        )
        _write_scalability(
            run_path / "scalability.csv", qet_by_circuit, mq_by_circuit
        )

    logging.info("Finished QET-vs-MorphQ comparison in %.2fs",
                 perf_counter() - started)
    return run_path



def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "QET vs MorphQ optimisation step comparison on QET benchmark."
        )
    )
    p.add_argument("--bench_path", type=str, default="benchmarks/arithmetic")
    p.add_argument("--tags", nargs="+", default=[])
    p.add_argument("--out", type=str, default=".outputs")
    p.add_argument("--log", type=int, default=logging.INFO)
    p.add_argument(
        "--shots", type=int, default=4096,
    )
    p.add_argument(
        "--alpha", type=float, default=0.05,
    )
    p.add_argument(
        "--max_qubits", type=int, default=20,
    )
    p.add_argument(
        "--circuit_id", nargs="+", default=None,
    )
    p.add_argument(
        "--max_inputs", type=int, default=None,
    )
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    logging.basicConfig(level=args.log)
    run_id = str(int(datetime.datetime.now().timestamp()))
    run_path = run_compare(
        run_id=run_id,
        tags=args.tags,
        base_out_dir=args.out,
        benchmark_path=args.bench_path,
        shots=args.shots,
        alpha=args.alpha,
        max_qubits=args.max_qubits,
        circuit_ids=args.circuit_id,
        max_inputs=args.max_inputs,
    )
    print(f"Results: {run_path}")
    print(f"  Per-circuit CSVs : {run_path}/<circuit_id>/{{qet,morphq,comparison}}.csv")
    print(f"  Per-circuit JSON : {run_path}/<circuit_id>/{{qet,morphq}}_summary.json")
    print(f"  Aggregates       : {run_path}/{{qet_all_rows,morphq_all_rows,comparison,combined_summary,scalability}}.csv")
    print(f"  Run summaries    : {run_path}/{{qet,morphq}}_summary.json")