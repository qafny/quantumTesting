import json
import os
from typing import List
from matplotlib import pyplot as plt
from qiskit import QuantumCircuit, transpile
from parser.qiskit import QiskitASTParser


def transpile_qiskit_circuit(qc: QuantumCircuit, gate_set: List[str], ignored_gate_set: List[str] = [], should_optimize: bool = False) -> QuantumCircuit:
    if should_optimize:
        return transpile(qc, basis_gates = gate_set + ignored_gate_set)

    return transpile(qc, basis_gates = gate_set + ignored_gate_set, optimization_level=0)


def parse_qiskit_circuit(qc: QuantumCircuit, gate_set: List[str], ignored_gate_set: List[str] = []) -> QuantumCircuit:
    tqc: QuantumCircuit = transpile_qiskit_circuit(qc, gate_set, ignored_gate_set)

    ast_parser = QiskitASTParser(tqc)
    return ast_parser.parse()


def read_qiskit_circuit(filename: str, circuit_name: str) -> QuantumCircuit:
    namespace = {}
    with open(filename, "r") as file:
        exec(file.read(), namespace)

    return namespace.get(circuit_name)


def read_qiskit_custom_benchmark(benchmark_folder: str) -> QuantumCircuit:
    config_file_path = os.path.join(benchmark_folder, ".config.json")
    if not os.path.exists(config_file_path):
        raise Exception(f"Config file not found at {config_file_path}")

    with open(config_file_path, "r") as config_file:
        config = json.load(config_file)

    circuit_file_name = config.get("circuit_file", None)
    circuit_name = config.get("circuit_name", None)

    if circuit_name is not None:
        if circuit_name is not None:
            circuit_file_path = os.path.join(benchmark_folder, circuit_file_name)
            return read_qiskit_circuit(circuit_file_path, circuit_name)
        else:
            raise Exception(f"No circuit_name found in config file at {config_file_path}")
    else:
        raise Exception(f"Circuit file not found in the config at {config_file_path}")


def visualize_qiskit_circuit(qc: QuantumCircuit, title: str):
    qc.draw(output="mpl")
    plt.show(title=title)
