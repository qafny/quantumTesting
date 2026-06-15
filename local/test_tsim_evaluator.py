import parser.utils.qiskit_utils as qiskit_utils
from evaluators.basis import CliffordTGateSetBasis
from evaluators.tsim import TSimEvaluator

benchmark_path = "benchmarks/testing/custom/oneh"

input_state = {
    "0": False,
    "1": False,
}

qc = qiskit_utils.read_qiskit_custom_benchmark(benchmark_path)
ast = qiskit_utils.parse_qiskit_circuit(qc, CliffordTGateSetBasis())
evaluator = TSimEvaluator(ast)
out_state = evaluator.evaluate(input_state)

print(out_state)
