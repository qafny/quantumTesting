from typing import Dict, List
from qiskit import QuantumCircuit
import parser.utils.qiskit_utils as qiskit_utils
from evaluators.basis import QETGateSetBasis
from qetast.markers import PrefixedHadamardGatesMarker, SuffixedHadamardGatesMarker, MeasureGateMarker
from qetast.printers import QuantumCircuitPrinter
from qetast.processors import MarkedNodeEliminator
from qetast.simulators import QETSimulator
import cmath

benchmark_path = "benchmarks/testing/custom/onex"


def create_state_from_bitvals(bitvals: List):
    state = {}
    for idx in range(len(bitvals)):
        state[str(idx)] = bitvals[idx]

    return state


def gen_basis_states(bitvals: List, outs: List[Dict], i: int):
    if i == len(bitvals) - 1:
        bitvals[i] = True
        outs.append(create_state_from_bitvals(bitvals))

        bitvals[i] = False
        outs.append(create_state_from_bitvals(bitvals))
    else:
        bitvals[i] = True
        gen_basis_states(bitvals, outs, i + 1)

        bitvals[i] = False
        gen_basis_states(bitvals, outs, i + 1)


def get_system_state_from_qubits(qubit_states: Dict[str, bool]):
    system_state = [(1 + 0j, qubit_states)]

    basis_states = []
    gen_basis_states([False] * len(qubit_states), basis_states, 0)
    for basis_state in basis_states:
        if basis_state != qubit_states:
            system_state.append((0 + 0j, basis_state))

    return system_state

qubit_states = {
    "0": False,
    "1": False,
}
system_state = get_system_state_from_qubits(qubit_states)

qc = qiskit_utils.read_qiskit_custom_benchmark(benchmark_path)
# qiskit_utils.visualize_qiskit_circuit(qc, title="Input QC")

ast = qiskit_utils.parse_qiskit_circuit(qc, QETGateSetBasis())

# pre_markers = [
#     PrefixedHadamardGatesMarker(),
#     SuffixedHadamardGatesMarker(),
#     MeasureGateMarker(),
# ]

pre_markers = []

for marker in pre_markers:
    ast = marker.visitRoot(ast)

pre_elims = [
    MarkedNodeEliminator(),
]

for elim in pre_elims:
    ast = elim.visitRoot(ast)


simulator = QETSimulator(system_state)
simulator.visitRoot(ast)

print(simulator.state)
print()

# printer = QuantumCircuitPrinter()
# printer.visitRoot(ast)

# qiskit_utils.visualize_qiskit_circuit(printer.qc, title="Output QC")
