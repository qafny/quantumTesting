"""Shared helpers for qc_to_xmlprogrammer_tests gate tests."""

import os
import sys
from pathlib import Path
from typing import Dict, List


def setup_project_paths() -> None:
    """Ensure repo root and qiskit-to-xmlprogrammer are importable."""
    here = Path(__file__).resolve().parent
    # .../qc_to_xmlprogrammer_tests/framework -> repo root is two levels up from here
    repo_root = str(here.parent.parent)
    translator_dir = os.path.join(repo_root, "qiskit-to-xmlprogrammer")

    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    if translator_dir not in sys.path:
        sys.path.append(translator_dir)


def compile_to_parse_tree(
    circuit,
    *,
    circuit_name: str = "Example Circuit",
    optimise_circuit: bool = False,
    show_decomposed_circuit: bool = True,
    gate_set_to_use=None,
):
    """Convert a Qiskit circuit to the XMLProgrammer parse tree."""
    from qiskit_to_xmlprogrammer import QCtoXMLProgrammer

    if gate_set_to_use is None:
        gate_set_to_use = []

    visitor = QCtoXMLProgrammer()
    return visitor.startVisit(
        circuit,
        circuitName=circuit_name,
        optimiseCircuit=optimise_circuit,
        showDecomposedCircuit=show_decomposed_circuit,
        gateSetToUse=gate_set_to_use,
    )


def build_input_state(state_bits: List[bool], include_output_qubit: bool = True) -> List[object]:
    """Build simulator input values from boolean bits."""
    from AST_Scripts.simulator import CoqNVal

    values = [CoqNVal(bit, phase=0) for bit in state_bits]
    if include_output_qubit:
        values.append(CoqNVal(False, phase=0))
    return values


def run_simulation(
    parse_tree,
    state_bits: List[bool],
    *,
    register_name: str = "test",
    include_output_qubit: bool = True,
) -> Dict[str, List[object]]:
    """Run simulator and return resulting state dictionary."""
    from AST_Scripts.simulator import Simulator

    values = build_input_state(state_bits, include_output_qubit=include_output_qubit)
    state = {register_name: values}
    environment = {register_name: len(values)}
    simulator = Simulator(state, environment)
    simulator.visitProgram(parse_tree)
    return simulator.state


def print_register_state(sim_state, register_name: str = "test") -> None:
    """Print register values in the same style as current tests."""
    from AST_Scripts.simulator import CoqNVal, CoqYVal

    for value in sim_state[register_name]:
        if isinstance(value, CoqNVal):
            print("bit", value.getBit())
        elif isinstance(value, CoqYVal):
            print("zero:", value.getZero())
            print("one:", value.getOne())
