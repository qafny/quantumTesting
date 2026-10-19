import argparse
import datetime
import logging
from typing import List, Dict, Any
import json
from pathlib import Path
from globals import TagProcessor
import qiskit
from qiskit import QuantumCircuit, qpy

from comparators.base import BaseComparator
from comparators.optimization_passes import OptimizationPassComparator
from evaluators.base import BaseEvaluator
from evaluators.passes import (
    Optimize1qGatesEvaluator,
    Optimize1qGatesDecompositionEvaluator, 
    Optimize1qGatesSimpleCommutationEvaluator,
    CommutativeInverseCancellationEvaluator,
    OptimizeCliffordsEvaluator,
    OptimizeCliffordTEvaluator,
    Split2QUnitariesEvaluator,
    CommutativeOptimizationEvaluator,
    TwoQubitPeepholeEvaluator
)
from readers.benchmarks import LibraryQiskitBenchmark, CustomQiskitBenchmark
from comparators.optimization_passes import OptimizationPassComparator
from writers.csv import ComparatorOutputCSVWriter
from writers.evaluators import EvaluatorParsedCircuitWriter
import helpers.argparsing as helper_args
from testers.base import BaseTester
from writers.csv import ComparatorOutputCSVWriter
from writers.evaluators import EvaluatorParsedCircuitWriter
from comparators.simplestate import SimpleStatePairwiseComparator, SimpleStateExpectedOutputComparator
from comparators.qucheck import QuCheckPropertiesPairwiseComparator, QuCheckExpectedPropertiesComparator

def parser_generator():
    parser = argparse.ArgumentParser(description="QET: Differential Testing of Quantum Programs across Target Platforms")
    parser.add_argument('--bench_path', type=str, default="benchmarks/arithmetic", help="Path to the Benchmark Folder")
    parser.add_argument('--tags', nargs='+', default=[], help="Tags for QET to represent different embedded functions. Refer to the readme.")
    parser.add_argument("--comp", type=str, default="spa", help="The comparator to use. Defaults to Simple Pairwise State Comparator")
    parser.add_argument("--evals", nargs='+', default=["qet", "tsim"], help="List of evaluators to run")
    parser.add_argument("--opt_level", type=int, default=0, help="The optimization level to use for the qiskit transpiler. Defaults to 0")
    parser.add_argument("--log", type=int, default=logging.DEBUG, help="Logging Level")
    parser.add_argument('--out', type=str, default=".outputs", help="Path to Store the Results")
    return parser.parse_args()

OPTIMIZATION_PASS_EVALUATORS = [
    Optimize1qGatesEvaluator,
    Optimize1qGatesDecompositionEvaluator,
    Optimize1qGatesSimpleCommutationEvaluator,
    CommutativeInverseCancellationEvaluator,
    OptimizeCliffordsEvaluator,
    OptimizeCliffordTEvaluator,
    Split2QUnitariesEvaluator,
    CommutativeOptimizationEvaluator,
    TwoQubitPeepholeEvaluator
]

def run_qet(run_id, tags, base_out_dir, benchmark_path, comparator_id,
            evaluator_ids, qiskit_opt_level):
    
    if any(tag in tags for tag in ("parse_rph", "parse_rsh", "parse_rm")):
        raise ValueError("Do not remove program operations in optimization-pass tests")
    TagProcessor().set_tags(tags=tags)
    if LibraryQiskitBenchmark.is_library_benchmark(benchmark_path):
        benchmark = LibraryQiskitBenchmark(benchmark_path)
    elif CustomQiskitBenchmark.is_custom_benchmark(benchmark_path):
        benchmark = CustomQiskitBenchmark(benchmark_path)
    else:
        raise ValueError(f"Unsupported benchmark: {benchmark_path}")

    csv_writer = ComparatorOutputCSVWriter(base_out_dir, benchmark_path, run_id)
    circuit_writer = EvaluatorParsedCircuitWriter(base_out_dir, benchmark_path, run_id)
    run_path = Path(csv_writer.get_run_path())
    (run_path / "run_metadata.json").write_text(json.dumps({
        "qiskit_version": qiskit.__version__, "benchmark_path": str(benchmark_path),
        "evaluators": [cls.get_identifier() for cls in OPTIMIZATION_PASS_EVALUATORS],
    }, indent=2) + "\n", encoding="utf-8")
    results = {}
    for circuit_id, info in benchmark.config["circuits"].items():
        comparator = None
        try:
            # Load only one circuit and input list at a time.
            circuit = benchmark.get_circuit_from_info(info)
            inputs = benchmark.get_inputs_from_info(info)
            comparator = OptimizationPassComparator(
                circuit=circuit, evaluator_classes=OPTIMIZATION_PASS_EVALUATORS,
                inputs=inputs,
            )
            rows = comparator.compare()
            generation = info.get("generation", {})
            for row in rows:
                row.update(circuit_id=circuit_id, family=generation.get("family", ""),
                           circuit_seed=generation.get("circuit_seed", ""),
                           input_seed=generation.get("input_seed", ""),
                           target_patterns=generation.get("target_patterns", ""),
                           inputs_count=len(inputs))
        except Exception as exc:
            logging.exception("Circuit failed: %s", circuit_id)
            rows = [{"circuit_id": circuit_id, "status": "ERROR",
                     "error": f"{type(exc).__name__}: {exc}"}]
        results[circuit_id] = rows
        # Persist before continuing to another circuit or saving artifacts.
        csv_writer.write({circuit_id: rows})
        artifact_errors = []
        if comparator is not None:
            for evaluator in comparator.get_evaluators():
                try:
                    circuit_writer.write(circuit_id, evaluator)
                    folder = run_path / circuit_id
                    with (folder / f"{evaluator.get_identifier()}.pass_output.qpy").open("wb") as file:
                        qpy.dump(evaluator.get_transformed_circuit(), file)
                except Exception as exc:
                    logging.exception("Artifact save failed for %s", circuit_id)
                    artifact_errors.append({"evaluator": evaluator.get_identifier(),
                                            "error": f"{type(exc).__name__}: {exc}"})
        if artifact_errors:
            (run_path / circuit_id / "artifact_errors.json").write_text(
                json.dumps(artifact_errors, indent=2) + "\n", encoding="utf-8")
    return results

def store_results(run_id: str, base_out_dir: str, benchmark_path: str, results: Dict[str, List[Dict[Any, Any]]]):
    logging.info("Storing Results")

    comp_outs_writer = ComparatorOutputCSVWriter(base_out_dir, benchmark_path, run_id)
    comp_outs_writer.write(results)

    logging.info("Finished Storing Results")


if __name__ == "__main__":
    run_id = str(int(datetime.datetime.now().timestamp()))

    args = parser_generator()

    logging.basicConfig(level=args.log)

    logging.info("Starting QET Differential Testing")
    results = run_qet(run_id, args.tags, args.out, args.bench_path, args.comp, args.evals, args.opt_level)

    logging.info(results)

    store_results(run_id, args.out, args.bench_path, results)

    logging.info("Finished QET Differential Testing")
