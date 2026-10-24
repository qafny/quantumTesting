"""MorphQ vs QET scalability comparison on randomly-generated programs.

Example usage: python -m comparators.morphq_compare \
        --qubits 32 64 \
        --num-gates 1000 5000 \
        --programs-per-config 100 \
        --inputs-count 1000 \
        --timeout 7200 \
        --out .outputs/scaling
"""

import argparse
import csv
import datetime
import json
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from program_generator.scaling_generator import (
    generate_random_inputs,
    generate_scaling_programs,
    write_benchmark,
)


_PASS_IMPORT_BLOCK = (
    "from evaluators.passes import ("
    " Optimize1qGatesEvaluator,"
    " Optimize1qGatesDecompositionEvaluator,"
    " Optimize1qGatesSimpleCommutationEvaluator,"
    " CommutativeInverseCancellationEvaluator,"
    " OptimizeCliffordsEvaluator,"
    " OptimizeCliffordTEvaluator,"
    " Split2QUnitariesEvaluator,"
    " CommutativeOptimizationEvaluator,"
    " TwoQubitPeepholeEvaluator,"
    ")"
)


def _load_pass_labels() -> Dict[str, str]:
    ns: Dict[str, Any] = {}
    exec(_PASS_IMPORT_BLOCK, ns)
    return {
        ns["Optimize1qGatesEvaluator"].get_identifier(): "Optimize1qGates",
        ns["Optimize1qGatesDecompositionEvaluator"].get_identifier(): "Optimize1qGatesDecomposition",
        ns["Optimize1qGatesSimpleCommutationEvaluator"].get_identifier(): "Optimize1qGatesSimpleCommutation",
        ns["CommutativeInverseCancellationEvaluator"].get_identifier(): "CommutativeInverseCancellation",
        ns["OptimizeCliffordsEvaluator"].get_identifier(): "OptimizeCliffords",
        ns["OptimizeCliffordTEvaluator"].get_identifier(): "OptimizeCliffordT",
        ns["Split2QUnitariesEvaluator"].get_identifier(): "Split2QUnitaries",
        ns["CommutativeOptimizationEvaluator"].get_identifier(): "CommutativeOptimization",
        ns["TwoQubitPeepholeEvaluator"].get_identifier(): "TwoQubitPeephole",
    }


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
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", restval="")
        w.writeheader()
        w.writerows(rows)


def _pick_failure_mode(counts: Dict[str, int]) -> str:
    non_success = {k: v for k, v in counts.items() if k != "SUCCESS"}
    if non_success:
        return max(non_success, key=non_success.get)
    return "worker_ok"


_OK_STATUSES = {"MATCH", "MISMATCH", "DIVERGED"}
_FAILED_STATUSES = {"ERROR", "REFERENCE_ERROR"}
_SKIPPED_STATUSES = {"SKIPPED"}


def _functional_status(row_statuses: List[str]) -> str:
    if not row_statuses or all(s == "" for s in row_statuses):
        return "no_rows"
    total = sum(1 for s in row_statuses if s)
    ok = sum(1 for s in row_statuses if s in _OK_STATUSES)
    failed = sum(1 for s in row_statuses if s in _FAILED_STATUSES)
    skipped = sum(1 for s in row_statuses if s in _SKIPPED_STATUSES)
    if total == 0:
        return "no_rows"
    if skipped == total:
        return "all_skipped"
    if ok == total:
        return "all_ok"
    if failed == total:
        return "all_failed"
    if ok == 0 and failed == 0 and skipped == total:
        return "all_skipped"
    return "partial"


def _effective_status(
    fw_counts: Dict[str, int],
    cfg_rows: List[Dict[str, Any]],
) -> str:
    if fw_counts.get("TIMEOUT", 0) > 0:
        return "TIMEOUT"
    if fw_counts.get("OOM", 0) > 0:
        return "OOM_KILLED"
    if any(k.startswith("SIGNAL_") and fw_counts[k] > 0 for k in fw_counts):
        return "SIGNAL_KILLED"
    if fw_counts.get("ERROR", 0) > 0:
        return "WORKER_ERROR"

    if fw_counts.get("OUT_OF_MEMORY_ALL", 0) > 0:
        return "OUT_OF_MEMORY"
    if fw_counts.get("ERRORED_ALL", 0) > 0:
        return "ALL_ERRORED"
    if fw_counts.get("SKIPPED_ALL", 0) > 0:
        return "SKIPPED"

    row_statuses = [r.get("row_status") or "" for r in cfg_rows]
    if not any(row_statuses):
        return "NO_RESULTS"
    oks = sum(1 for s in row_statuses if s in _OK_STATUSES)
    if oks == len(row_statuses):
        return "OK"
    if oks > 0:
        return "PARTIAL_OK"
    return "NO_RESULTS"

def _run_worker(
    project_root: Path,
    framework: str,
    bench_path: Path,
    circuit_id: str,
    output_json: Path,
    timeout: float,
    shots: int,
    alpha: float,
) -> Dict[str, Any]:
    cmd = [
        sys.executable, "-u", "-m", "comparators._scaling_worker",
        framework, str(bench_path), circuit_id, str(output_json),
        f"--shots={shots}", f"--alpha={alpha}",
    ]

    log_path = output_json.parent / f"{framework}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    started = time.perf_counter()
    with log_path.open("wb") as log_file:
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(project_root),
                stdout=log_file,
                stderr=subprocess.STDOUT,
                start_new_session=(os.name == "posix"),
            )
        except Exception as exc:
            return {
                "status": "ERROR", "elapsed_s": 0.0, "rows": [],
                "error": f"{type(exc).__name__}: {exc}",
                "log_path": str(log_path),
            }

        timed_out = False
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            if os.name == "posix":
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            else:
                proc.kill()
            proc.wait()
    elapsed = time.perf_counter() - started

    if output_json.exists():
        try:
            payload = json.loads(output_json.read_text())
        except Exception:
            payload = {"status": "ERROR", "rows": [],
                       "error": "invalid worker json"}
        payload["elapsed_s"] = payload.get("elapsed_s", elapsed)
        payload["returncode"] = proc.returncode
        payload["log_path"] = str(log_path)
        if timed_out:
            payload["status"] = "TIMEOUT"
            payload.setdefault("error", f"exceeded {timeout}s")
        return payload

    rc = proc.returncode
    if rc is not None and rc < 0:
        sig = abs(rc)
        if not timed_out and sig == 9:
            status = "OOM"
            error = (
                f"worker killed by SIGKILL (likely OOM killer); "
                f"see {log_path.name}"
            )
        else:
            status = f"SIGNAL_{sig}"
            error = f"worker killed by signal {sig}; see {log_path.name}"
    elif timed_out:
        status = "TIMEOUT"
        error = f"exceeded {timeout}s (see {log_path.name})"
    else:
        status = "ERROR"
        error = f"worker exited with code {rc}"
    return {
        "status": status, "elapsed_s": elapsed, "rows": [],
        "error": error, "returncode": rc, "log_path": str(log_path),
    }


def _flatten_framework_result(
    framework: str,
    circuit_id: str,
    num_qubits: int,
    num_gates: int,
    payload: Dict[str, Any],
    pass_labels: Dict[str, str],
) -> List[Dict[str, Any]]:
    framework_status = payload.get("status", "UNKNOWN")
    elapsed = payload.get("elapsed_s", "")
    framework_error = payload.get("error", "") or ""
    rows = payload.get("rows") or []

    if not rows:
        return [{
            "framework": framework,
            "circuit_id": circuit_id,
            "num_qubits": num_qubits,
            "num_gates_target": num_gates,
            "pass_id": "",
            "pass_name": "",
            "input_index": "",
            "framework_status": framework_status,
            "row_status": "",
            "row_error": "",
            "elapsed_total_s": elapsed,
            "framework_error": framework_error,
        }]

    out = []
    for row in rows:
        pass_id = row.get("evaluator", "") or ""
        out.append({
            "framework": framework,
            "circuit_id": circuit_id,
            "num_qubits": num_qubits,
            "num_gates_target": num_gates,
            "pass_id": pass_id,
            "pass_name": pass_labels.get(pass_id, pass_id),
            "input_index": row.get("input_index", ""),
            "framework_status": framework_status,
            "row_status": row.get("status", "") or "",
            "row_error": row.get("error", "") or "",
            "elapsed_total_s": elapsed,
            "framework_error": framework_error,
            "transform_s": row.get("transform_s", ""),
            "simulation_s": row.get("simulation_s", ""),
            "comparison_s": row.get("comparison_s", ""),
        })
    return out


def _build_summary(
    all_rows: List[Dict[str, Any]],
    metadata: Dict[str, Any],
) -> Dict[str, Any]:
    framework_status_counts: Dict[tuple, Dict[str, int]] = {}
    pass_counts: Dict[tuple, Dict[str, int]] = {}
    programs_by_key: Dict[tuple, set] = {}

    def _bump(d: Dict[tuple, Dict[str, int]], key: tuple, name: str) -> None:
        d.setdefault(key, {})
        d[key][name] = d[key].get(name, 0) + 1

    for row in all_rows:
        fw = row["framework"]
        fw_key = (fw, row["num_qubits"], row["num_gates_target"])
        _bump(framework_status_counts, fw_key, row["framework_status"])
        programs_by_key.setdefault(fw_key, set()).add(row["circuit_id"])
        if row.get("pass_name"):
            p_key = (fw, row["num_qubits"], row["num_gates_target"],
                     row["pass_name"])
            _bump(pass_counts, p_key, row.get("row_status") or "UNKNOWN")

    by_config: List[Dict[str, Any]] = []
    for (fw, q, g), fw_counts in sorted(framework_status_counts.items()):
        cfg_rows = [
            r for r in all_rows
            if r["framework"] == fw
            and r["num_qubits"] == q
            and r["num_gates_target"] == g
        ]
        row_statuses = [r.get("row_status") or "" for r in cfg_rows]
        rows_ok = sum(1 for s in row_statuses if s in _OK_STATUSES)
        rows_failed = sum(1 for s in row_statuses if s in _FAILED_STATUSES)
        rows_skipped = sum(1 for s in row_statuses if s in _SKIPPED_STATUSES)

        fw_errors = [r["framework_error"] for r in cfg_rows
                     if r.get("framework_error")]
        row_errors = [r["row_error"] for r in cfg_rows
                      if r.get("row_error")]
        first_row_error = row_errors[0][:250] if row_errors else ""

        by_config.append({
            "framework": fw,
            "num_qubits": q,
            "num_gates": g,
            "programs": len(programs_by_key[(fw, q, g)]),
            "runs": sum(fw_counts.values()),
            "framework_success": fw_counts.get("SUCCESS", 0),
            "framework_timeout": fw_counts.get("TIMEOUT", 0),
            "framework_oom": fw_counts.get("OOM", 0),
            "framework_skipped_all": fw_counts.get("SKIPPED_ALL", 0),
            "framework_oom_all": fw_counts.get("OUT_OF_MEMORY_ALL", 0),
            "framework_errored_all": fw_counts.get("ERRORED_ALL", 0),
            "framework_error": fw_counts.get("ERROR", 0),
            "failure_mode": _pick_failure_mode(fw_counts),
            "effective_status": _effective_status(fw_counts, cfg_rows),
            "rows_total": len(row_statuses),
            "rows_ok": rows_ok,
            "rows_failed": rows_failed,
            "rows_skipped": rows_skipped,
            "functional_status": _functional_status(row_statuses),
            "first_framework_error": fw_errors[0] if fw_errors else "",
            "first_row_error": first_row_error,
        })

    by_pass: List[Dict[str, Any]] = []
    for (fw, q, g, pname), counts in sorted(pass_counts.items()):
        by_pass.append({
            "framework": fw,
            "num_qubits": q,
            "num_gates": g,
            "pass_name": pname,
            "rows": sum(counts.values()),
            "matched": counts.get("MATCH", 0),
            "mismatched": counts.get("MISMATCH", 0),
            "diverged": counts.get("DIVERGED", 0),
            "errored": counts.get("ERROR", 0)
                       + counts.get("REFERENCE_ERROR", 0),
            "skipped": counts.get("SKIPPED", 0),
        })

    return {
        "metadata": metadata,
        "by_config": by_config,
        "by_pass": by_pass,
    }

def _run_scaling(args: argparse.Namespace, run_dir: Path) -> None:
    pass_labels = _load_pass_labels()
    project_root = Path.cwd()

    metadata = {
        "run_id": run_dir.name,
        "mode": "scaling",
        "qubits": args.qubits,
        "gates": args.num_gates,
        "programs_per_config": args.programs_per_config,
        "inputs_count": args.inputs_count,
        "timeout_s": args.timeout,
        "shots": args.shots,
        "alpha": args.alpha,
        "frameworks": args.frameworks,
        "seed": args.seed,
        "pass_labels": pass_labels,
    }
    (run_dir / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    all_rows: List[Dict[str, Any]] = []

    for q in args.qubits:
        for g in args.num_gates:
            cfg_dir = run_dir / f"q{q}_g{g}"
            cfg_dir.mkdir(parents=True, exist_ok=True)
            print(f"\n=== q={q}  gates={g} ===", flush=True)

            programs = generate_scaling_programs(
                num_qubits=q,
                num_gates=g,
                n_samples=args.programs_per_config,
                seed=args.seed,
            )

            for prog_idx, program in enumerate(programs):
                circuit_id = f"q{q}_g{g}_prog{prog_idx:03d}"
                case_dir = cfg_dir / circuit_id
                bench_dir = case_dir / "benchmark"

                inputs = generate_random_inputs(
                    num_qubits=q,
                    count=args.inputs_count,
                    seed=args.seed + prog_idx,
                )
                write_benchmark(bench_dir, circuit_id, program, inputs)

                for framework in args.frameworks:
                    out_json = case_dir / f"{framework}.json"
                    print(f"  [{framework}] {circuit_id} ... ",
                          end="", flush=True)
                    payload = _run_worker(
                        project_root=project_root,
                        framework=framework,
                        bench_path=bench_dir,
                        circuit_id=circuit_id,
                        output_json=out_json,
                        timeout=args.timeout,
                        shots=args.shots,
                        alpha=args.alpha,
                    )
                    row_outcomes = [r.get("status", "") for r in payload.get("rows", [])]
                    if row_outcomes:
                        fstat = _functional_status(row_outcomes)
                        print(f"{payload['status']} ({fstat})", flush=True)
                    else:
                        print(payload["status"], flush=True)

                    all_rows.extend(_flatten_framework_result(
                        framework=framework,
                        circuit_id=circuit_id,
                        num_qubits=q,
                        num_gates=g,
                        payload=payload,
                        pass_labels=pass_labels,
                    ))

            cfg_rows = [
                r for r in all_rows
                if r["num_qubits"] == q
                and r["num_gates_target"] == g
            ]
            _write_csv(cfg_dir / "all_rows.csv", cfg_rows)

    _write_csv(run_dir / "all_rows.csv", all_rows)

    summary = _build_summary(all_rows, metadata)
    (run_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    _write_csv(run_dir / "summary_by_config.csv", summary["by_config"])
    _write_csv(run_dir / "summary_by_pass.csv", summary["by_pass"])

    print(f"\nResults: {run_dir}")
    print(f"  run_metadata.json     : {run_dir / 'run_metadata.json'}")
    print(f"  summary.json          : {run_dir / 'summary.json'}")
    print(f"  summary_by_config.csv : {run_dir / 'summary_by_config.csv'}")
    print(f"  summary_by_pass.csv   : {run_dir / 'summary_by_pass.csv'}")
    print(f"  all_rows.csv          : {run_dir / 'all_rows.csv'}")


def _run_benchmark(args: argparse.Namespace, run_dir: Path) -> None:
    from readers.benchmarks import (
        LibraryQiskitBenchmark, CustomQiskitBenchmark,
    )
    from comparators.optimization_passes import OptimizationPassComparator
    from comparators.morphq_opt import MorphQOptimisationPassComparator

    pass_labels = _load_pass_labels()
    ns: Dict[str, Any] = {}
    exec(_PASS_IMPORT_BLOCK, ns)
    evaluator_classes = [
        ns["Optimize1qGatesEvaluator"],
        ns["Optimize1qGatesDecompositionEvaluator"],
        ns["Optimize1qGatesSimpleCommutationEvaluator"],
        ns["CommutativeInverseCancellationEvaluator"],
        ns["OptimizeCliffordsEvaluator"],
        ns["OptimizeCliffordTEvaluator"],
        ns["Split2QUnitariesEvaluator"],
        ns["CommutativeOptimizationEvaluator"],
        ns["TwoQubitPeepholeEvaluator"],
    ]

    bench_path = args.bench_path
    if LibraryQiskitBenchmark.is_library_benchmark(bench_path):
        benchmark = LibraryQiskitBenchmark(bench_path)
    elif CustomQiskitBenchmark.is_custom_benchmark(bench_path):
        benchmark = CustomQiskitBenchmark(bench_path)
    else:
        raise ValueError(f"Unsupported benchmark: {bench_path}")

    all_rows: List[Dict[str, Any]] = []
    for circuit_id, info in benchmark.config["circuits"].items():
        circuit = benchmark.get_circuit_from_info(info)
        inputs = benchmark.get_inputs_from_info(info)

        for framework, cls in (
            ("qet", OptimizationPassComparator),
            ("morphq", MorphQOptimisationPassComparator),
        ):
            try:
                if framework == "qet":
                    cmp = cls(
                        circuit=circuit,
                        evaluator_classes=evaluator_classes,
                        inputs=inputs,
                    )
                else:
                    cmp = cls(
                        circuit=circuit,
                        evaluator_classes=evaluator_classes,
                        inputs=inputs,
                        shots=args.shots,
                        alpha=args.alpha,
                    )
                rows = cmp.compare()
                payload = {
                    "status": "SUCCESS", "elapsed_s": 0.0, "rows": rows,
                }
            except Exception as exc:
                payload = {
                    "status": "ERROR", "elapsed_s": 0.0, "rows": [],
                    "error": f"{type(exc).__name__}: {exc}",
                }

            all_rows.extend(_flatten_framework_result(
                framework=framework,
                circuit_id=circuit_id,
                num_qubits=circuit.num_qubits,
                num_gates=circuit.size(),
                payload=payload,
                pass_labels=pass_labels,
            ))

    _write_csv(run_dir / "all_rows.csv", all_rows)

    summary = _build_summary(all_rows, {
        "mode": "benchmark",
        "bench_path": str(bench_path),
        "shots": args.shots,
        "alpha": args.alpha,
    })
    (run_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    _write_csv(run_dir / "summary_by_config.csv", summary["by_config"])
    _write_csv(run_dir / "summary_by_pass.csv", summary["by_pass"])
    print(f"\nResults: {run_dir}")


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--mode", choices=["scaling", "benchmark"],
                        default="scaling")
    parser.add_argument("--out", default=".outputs")
    parser.add_argument("--log", type=int, default=logging.INFO)
    parser.add_argument("--seed", type=int, default=42)

    parser.add_argument("--qubits", nargs="+", type=int, default=[32, 64])
    parser.add_argument("--num-gates", nargs="+", type=int, default=[10000, 50000])
    parser.add_argument("--programs-per-config", type=int, default=3)
    parser.add_argument("--inputs-count", type=int, default=5)
    parser.add_argument("--num-h-gates", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--frameworks", nargs="+", default=["qet", "morphq"],
                        choices=["qet", "morphq"])

    parser.add_argument("--shots", type=int, default=1000)
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument(
        "--max-qubits", type=int, default=None,
        help="Optional MorphQ pre-flight limit. Leave unset so MorphQ "
             "genuinely attempts 32q/64q programs and fails empirically.",
    )

    parser.add_argument("--bench_path", default=None)
    args = parser.parse_args(argv)

    logging.basicConfig(level=args.log)

    run_id = datetime.datetime.now().strftime("%Y%m%dT%H%M%S_%f")
    run_dir = Path(args.out) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    if args.mode == "benchmark":
        if not args.bench_path:
            parser.error("--mode benchmark requires --bench_path")
        _run_benchmark(args, run_dir)
    else:
        if args.timeout <= 0:
            parser.error("--timeout must be positive")
        if args.programs_per_config <= 0:
            parser.error("--programs-per-config must be positive")
        if args.inputs_count <= 0:
            parser.error("--inputs-count must be positive")
        _run_scaling(args, run_dir)

if __name__ == "__main__":
    main()