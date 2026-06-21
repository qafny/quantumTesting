import json
from pathlib import Path
from evaluators.base import BaseEvaluator
from evaluators.basis import GateSetBasis
from writers.base import BaseWriter
from qiskit import qpy


class EvaluatorParsedCircuitWriter(BaseWriter):

    def __init__(self, base_path: str, benchmark_path: str, run_id: str):
        super(EvaluatorParsedCircuitWriter, self).__init__(base_path, benchmark_path, run_id)

    def get_gateset_representation(self, gate_set: GateSetBasis):
        gates_str = []
        for gate, _ in gate_set.get_gate_set():
            gates_str.append(gate.name)

        for gate, _, _ in gate_set.get_custom_gate_definitions():
            gates_str.append(gate.name)

        return gates_str

    def write(self, circuit_id: str, evaluator: BaseEvaluator):
        circuit_path = f"{self.get_run_path()}/{circuit_id}"
        Path(circuit_path).mkdir(parents=True, exist_ok=True)

        qpy_path = f"{circuit_path}/{evaluator.get_identifier()}.qpy"
        with open(qpy_path, "wb") as qpy_file:
            qpy.dump(evaluator.get_parsed_circuit(), qpy_file)

        props = {
            "evaluator": evaluator.get_identifier(),
            "gate_set": self.get_gateset_representation(evaluator.get_gateset_basis()),
            "num_qubits": evaluator.get_parsed_circuit().num_qubits,
            "gates_count": evaluator.get_parsed_circuit().size(),
        }

        props_path = f"{qpy_path}.json"
        with open(props_path, "w") as props_file:
            json.dump(props, props_file)
