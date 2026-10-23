"""Runs one (benchmark, framework) pair and dumps JSON.

Usage: python -m comparators._scaling_worker <framework> <bench_path> <circuit_id> <output_json> [--shots=N] [--alpha=A]
"""

import argparse
import json
import time
import traceback
from pathlib import Path
from globals import TagProcessor
TagProcessor().set_tags(tags=[])


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

def _load_pass_evaluators():
    ns = {}
    exec(_PASS_IMPORT_BLOCK, ns)
    return [
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

def _load_benchmark(bench_path: str):
    from readers.benchmarks import (
        LibraryQiskitBenchmark, CustomQiskitBenchmark,
    )
    if LibraryQiskitBenchmark.is_library_benchmark(bench_path):
        return LibraryQiskitBenchmark(bench_path)
    if CustomQiskitBenchmark.is_custom_benchmark(bench_path):
        return CustomQiskitBenchmark(bench_path)
    raise ValueError(f"Unsupported benchmark: {bench_path}")

def _json_safe(v):
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    if isinstance(v, dict):
        return {str(k): _json_safe(val) for k, val in v.items()}
    if isinstance(v, (list, tuple, set)):
        return [_json_safe(x) for x in v]
    if isinstance(v, complex):
        return [v.real, v.imag]
    return str(v)

def _run(framework, circuit, inputs, evaluator_classes, shots, alpha,):
    if framework == "qet":
        from comparators.optimization_passes import (
            OptimizationPassComparator,
        )
        comparator = OptimizationPassComparator(
            circuit=circuit,
            evaluator_classes=evaluator_classes,
            inputs=inputs,
        )
        return comparator.compare()

    from comparators.morphq_opt import MorphQOptimisationPassComparator
    comparator = MorphQOptimisationPassComparator(
        circuit=circuit,
        evaluator_classes=evaluator_classes,
        inputs=inputs,
        shots=shots,
        alpha=alpha,
    )
    return comparator.compare()


def _classify_row_outcome(rows):
    if not rows:
        return None
    statuses = [r.get("status") for r in rows]
    if all(s == "SKIPPED" for s in statuses):
        return "SKIPPED_ALL"
    if all(s in ("ERROR", "REFERENCE_ERROR") for s in statuses):
        all_mem = all(
            "memory" in str(r.get("error") or "").lower()
            for r in rows
        )
        return "OUT_OF_MEMORY_ALL" if all_mem else "ERRORED_ALL"
    return None

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("framework", choices=["qet", "morphq"])
    parser.add_argument("bench_path")
    parser.add_argument("circuit_id")
    parser.add_argument("output_json")
    parser.add_argument("--shots", type=int, default=1000)
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--max-qubits", type=int, default=None,)
    args = parser.parse_args(argv)
    TagProcessor().set_tags(tags=[])
    start = time.perf_counter()
    result = {"status": "SUCCESS", "elapsed_s": None, "rows": []}
    try:
        benchmark = _load_benchmark(args.bench_path)
        info = benchmark.config["circuits"][args.circuit_id]
        circuit = benchmark.get_circuit_from_info(info)
        inputs = benchmark.get_inputs_from_info(info)
        evaluator_classes = _load_pass_evaluators()
        rows = _run(
            args.framework, circuit, inputs, evaluator_classes, shots=args.shots, alpha=args.alpha,
        )
        coarse = _classify_row_outcome(rows)
        if coarse is not None:
            result["status"] = coarse
        result["rows"] = _json_safe(rows)
    except MemoryError as exc:
        result["status"] = "OOM"
        result["error"] = str(exc)
    except Exception as exc:
        result["status"] = "ERROR"
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc()

    result["elapsed_s"] = time.perf_counter() - start
    Path(args.output_json).write_text(
        json.dumps(result), encoding="utf-8")

if __name__ == "__main__":
    main()