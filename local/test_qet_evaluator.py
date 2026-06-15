import parser.utils.qiskit_utils as qiskit_utils
from evaluators.qet import QETEvaluator

benchmark_path = "benchmarks/testing/custom/oneh"

input_state = {
    "0": False,
    "1": False,
}

qc = qiskit_utils.read_qiskit_custom_benchmark(benchmark_path)
evaluator = QETEvaluator(qc)
out_state = evaluator.evaluate(input_state)

print(out_state)
