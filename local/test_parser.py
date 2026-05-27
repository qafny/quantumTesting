import parser.utils.qiskit_utils as qiskit_utils
from evaluators.basis import QiskitBasis
from qetast.printers import QuantumCircuitPrinter
from qetast.processors import PrecedingHadamardEliminationProcessor, SucceedingHadamardEliminationProcessor

benchmark_path = "benchmarks/custom/ghz"

qc = qiskit_utils.read_qiskit_custom_benchmark(benchmark_path)
qiskit_utils.visualize_qiskit_circuit(qc, title="Input QC")

ast = qiskit_utils.parse_qiskit_circuit(qc, QiskitBasis())

procs = [
    PrecedingHadamardEliminationProcessor(),
    SucceedingHadamardEliminationProcessor(),
]

for ctr in procs:
    ast = ctr.visitRoot(ast)

printer = QuantumCircuitPrinter()
printer.visitRoot(ast)

qiskit_utils.visualize_qiskit_circuit(printer.qc, title="Output QC")
