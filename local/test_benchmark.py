import parser.utils.benchmark_utils as benchmark_utils
from evaluators.basis import QiskitBasis
from parser.utils import qiskit_utils
from qetast.printers import QuantumCircuitPrinter
from qetast.processors import PrecedingHadamardEliminationProcessor, SucceedingHadamardEliminationProcessor

benchmark_path = "benchmarks/grover_operator"

circuits = benchmark_utils.read_benchmark(benchmark_path)
qc = circuits[0]
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
