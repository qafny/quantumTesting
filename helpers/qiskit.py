import logging
from typing import Tuple
from qiskit import QuantumCircuit, transpile
from qiskit.transpiler import Target
from evaluators.basis import GateSetBasis
from parser.qiskit import QiskitASTParser
from qetast.nodes import QXRoot


def transpile_qiskit_circuit(qc: QuantumCircuit, basis: GateSetBasis, optimization_level: int) -> QuantumCircuit:
    target = Target()

    for gate, props in basis.get_gate_set():
        target.add_instruction(gate, props)

    for gate, props, gate_name in basis.get_custom_gate_definitions():
        target.add_instruction(gate, props, name = gate_name)

    transpiled_qc = transpile(qc, target = target, optimization_level = optimization_level)

    return transpiled_qc


def parse_qiskit_circuit(qc: QuantumCircuit, basis: GateSetBasis, optimization_level: int) -> Tuple[QuantumCircuit, QXRoot]:
    logging.info("Transpiling Qiskit Circuit")
    tqc: QuantumCircuit = transpile_qiskit_circuit(qc, basis, optimization_level)
    logging.info("Finished Transpiling Qiskit Circuit")
    logging.debug(f"tqc qubit count = {tqc.num_qubits}, tqc gates count = {tqc.size()}")

    logging.info("Parsing AST from the Transpiled Circuit")
    ast_parser = QiskitASTParser(tqc)
    ast = ast_parser.parse()
    logging.info("Finished Parsing AST from the Transpiled Circuit")
    return tqc, ast
