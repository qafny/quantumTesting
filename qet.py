import argparse
import datetime
import logging
from typing import List, Dict, Any
from qiskit import QuantumCircuit
from comparators.base import BaseComparator
from evaluators.base import BaseEvaluator
from readers.benchmarks import LibraryQiskitBenchmark, CustomQiskitBenchmark
import helpers.argparsing as helper_args
from writers.csv import ComparatorOutputCSVWriter
from writers.evaluators import EvaluatorParsedCircuitWriter


def parser_generator():
    parser = argparse.ArgumentParser(description="QET: Differential Testing of Quantum Programs across Target Platforms")
    parser.add_argument('--bench_path', type=str, default="benchmarks/arithmetic", help="Path to the Benchmark Folder")
    parser.add_argument("--comp", type=str, default="spa", help="The comparator to use. Defaults to Simple Pairwise State Comparator")
    parser.add_argument("--evals", nargs='+', default=["qet", "tsim"], help="List of evaluators to run")
    parser.add_argument("--log", type=int, default=logging.DEBUG, help="Logging Level")
    parser.add_argument('--out', type=str, default=".outputs", help="Path to Store the Results")

    return parser.parse_args()


def run_qet(run_id: str, base_out_dir: str, benchmark_path: str, comparator_id: str, evaluator_ids: List[str]):
    logging.info(f"Reading Benchmark: {benchmark_path}")

    if LibraryQiskitBenchmark.is_library_benchmark(benchmark_path):
        benchmark = LibraryQiskitBenchmark(benchmark_path)
    elif CustomQiskitBenchmark.is_custom_benchmark(benchmark_path):
        benchmark = CustomQiskitBenchmark(benchmark_path)
    else:
        raise Exception(f"Benchmark {benchmark_path} is not found/not supported")

    circuits: Dict[str, QuantumCircuit] = benchmark.get_qiskit_circuits()
    inputs: Dict[str, List[Dict[str, bool]]] = benchmark.get_inputs()

    logging.info(f"Read Circuits Count: {len(circuits)}")
    logging.info(f"Read Inputs Count: {len(inputs)}")

    evaluator_classes: List[type[BaseEvaluator]] = helper_args.parse_evaluators_list(evaluator_ids)
    comparator_class: type[BaseComparator] = helper_args.parse_comparator(comparator_id)

    logging.info("Start Testing")

    pc_writer = EvaluatorParsedCircuitWriter(base_out_dir, benchmark_path, run_id)

    outs = {}
    for circuit_id in circuits.keys():
        logging.info(f"Testing Circuit: {circuit_id}")

        circuit = circuits[circuit_id]
        circuit_inputs = inputs[circuit_id]

        evaluators: List[BaseEvaluator] = [evaluator_class(circuit) for evaluator_class in evaluator_classes]
        comparator: BaseComparator = comparator_class(evaluators, circuit_inputs)

        logging.info("Storing Parsed Circuits")
        for evaluator in evaluators:
            pc_writer.write(circuit_id, evaluator)
        logging.info("Finished Storing Parsed Circuits")

        outs[circuit_id] = comparator.compare()

        logging.info(f"Finished Testing Circuit: {circuit_id}")

    return outs


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
    results = run_qet(run_id, args.out, args.bench_path, args.comp, args.evals)

    print(results)

    store_results(run_id, args.out, args.bench_path, results)

    logging.info("Finished QET Differential Testing")
