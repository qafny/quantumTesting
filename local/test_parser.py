import parser.utils.qiskit_utils as qiskit_utils
from evaluators.basis import QETGateSetBasis
from qetast.markers import PrefixedHadamardGatesMarker, SuffixedHadamardGatesMarker, MeasureGateMarker
from qetast.printers import QuantumCircuitPrinter
from qetast.processors import MarkedNodeEliminator

benchmark_path = "benchmarks/custom/ghz"

qc = qiskit_utils.read_qiskit_custom_benchmark(benchmark_path)
qiskit_utils.visualize_qiskit_circuit(qc, title="Input QC")

ast = qiskit_utils.parse_qiskit_circuit(qc, QETGateSetBasis())

pre_markers = [
    PrefixedHadamardGatesMarker(),
    SuffixedHadamardGatesMarker(),
    MeasureGateMarker(),
]

for marker in pre_markers:
    ast = marker.visitRoot(ast)

pre_elims = [
    MarkedNodeEliminator(),
]

for elim in pre_elims:
    ast = elim.visitRoot(ast)

printer = QuantumCircuitPrinter()
printer.visitRoot(ast)

qiskit_utils.visualize_qiskit_circuit(printer.qc, title="Output QC")
