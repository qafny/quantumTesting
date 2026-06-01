from evaluators.basis import CliffordTGateSetBasis
from parser.utils import benchmark_utils, qiskit_utils
from qetast.printers import TSimPrinter, QuantumCircuitPrinter
from qetast.values import CoqNVal

benchmark_path = "benchmarks/cdkm_ripple_carry_adder"
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

ast = qiskit_utils.parse_qiskit_circuit(qc, CliffordTGateSetBasis())

ast_printer = QuantumCircuitPrinter()
ast_printer.visitRoot(ast)

qiskit_utils.visualize_qiskit_circuit(ast_printer.qc, title="AST")

printer = TSimPrinter()
printer.visitRoot(ast)

program = printer.tsim_program

print(program)
