import parser.utils.benchmark_utils as benchmark_utils
from evaluators.basis import QETGateSetBasis
from parser.utils import qiskit_utils
from qetast.printers import QuantumCircuitPrinter
from qetast.markers import PrefixedHadamardGatesMarker, SuffixedHadamardGatesMarker, AllHadamardGatesMarker
from qetast.processors import MarkedNodeEliminator
from qetast.simulators import QETSimulator
from qetast.values import CoqNVal

benchmark_path = "benchmarks/grover_operator"
initial_state = {
    "0": CoqNVal(False, 0),
    "1": CoqNVal(False, 0),
    "2": CoqNVal(False, 0),
    "3": CoqNVal(False, 0),
}
initial_env = {}

circuits = benchmark_utils.read_benchmark(benchmark_path)
qc = circuits[0]
qiskit_utils.visualize_qiskit_circuit(qc, title="Input QC")

ast = qiskit_utils.parse_qiskit_circuit(qc, QETGateSetBasis())

pre_markers = [
    PrefixedHadamardGatesMarker(),
    SuffixedHadamardGatesMarker(),
]

for marker in pre_markers:
    ast = marker.visitRoot(ast)

pre_elims = [
    MarkedNodeEliminator(),
]

for elim in pre_elims:
    ast = elim.visitRoot(ast)

# Partitioned Evaluation
ah_marker = AllHadamardGatesMarker()
ast = ah_marker.visitRoot(ast)

printer = QuantumCircuitPrinter()
printer.visitRoot(ast)

qiskit_utils.visualize_qiskit_circuit(printer.qc, title="Output QC")

simulator = QETSimulator(initial_state, initial_env)
simulator.visitRoot(ast)

print(simulator.state)
