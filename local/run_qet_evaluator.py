import parser.utils.qiskit_utils as qiskit_utils
from evaluators.qet import QETEvaluator

benchmark_path = "benchmarks/testing/custom/onecu"

input_state = {
    "0": True,
    "1": False,
}

qc = qiskit_utils.read_qiskit_custom_benchmark(benchmark_path)
evaluator = QETEvaluator(qc)
out_state = evaluator.evaluate(input_state)

print(out_state)
