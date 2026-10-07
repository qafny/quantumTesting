import logging

from qiskit import QuantumCircuit
from qiskit.transpiler import PassManager
from qiskit.transpiler.passes import Optimize1qGates

from evaluators.qet import QETEvaluator


class Optimize1qGatesEvaluator(QETEvaluator):

    def __init__(self, qc: QuantumCircuit, **kwargs):
        logging.info("Initializing Optimize1qGatesEvaluator")

        self._original_circuit = qc.copy()

        # Run only the component we are testing.
        pass_manager = PassManager([
            Optimize1qGates(basis=["p", "u"])
        ])

        self._pass_output_circuit = pass_manager.run(qc.copy())

        logging.info(
            "Optimize1qGates: gate count %d -> %d",
            self._original_circuit.size(),
            self._pass_output_circuit.size(),
        )
        logging.info(
            "Direct Optimize1qGates output:\n%s",
            self._pass_output_circuit.draw(output="text")
        )

        # Translate a copy into QET's supported basis and construct its AST.
        # This is preparation for simulation, after the tested pass has run.
        super().__init__(
            qc=self._pass_output_circuit.copy(),
            optimization_level=0,
        )

    @staticmethod
    def get_identifier() -> str:
        return "opt1q"

    def get_original_circuit(self) -> QuantumCircuit:
        return self._original_circuit

    def get_pass_output_circuit(self) -> QuantumCircuit:
        return self._pass_output_circuit