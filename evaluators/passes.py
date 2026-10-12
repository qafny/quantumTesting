import logging

from qiskit import QuantumCircuit
from qiskit.transpiler import (
    PassManager,
    Target,
    InstructionProperties
)
from qiskit.circuit import Parameter
from qiskit.circuit.library import UGate, CXGate
from qiskit.transpiler.passes import (
    Optimize1qGates, 
    Optimize1qGatesDecomposition,
    Optimize1qGatesSimpleCommutation,
    OptimizeCliffords,
    OptimizeCliffordT,
    CommutativeInverseCancellation,
    Split2QUnitaries,
    TwoQubitPeepholeOptimization,
    CommutativeOptimization
)

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

class Optimize1qGatesEvaluator(QETEvaluator):

    def __init__(self, qc: QuantumCircuit, **kwargs):
        self._transformed_circuit = self.transform(qc)

        super().__init__(
            qc=self._transformed_circuit.copy(),
            optimization_level=0,
        )

    def transform(self, circuit: QuantumCircuit) -> QuantumCircuit:
        manager = PassManager([
            Optimize1qGates(basis=["p", "u"])
        ])
        return manager.run(circuit.copy())

    def get_transformed_circuit(self) -> QuantumCircuit:
        return self._transformed_circuit

    @staticmethod
    def get_identifier() -> str:
        return "opt1q"

class Optimize1qGatesDecompositionEvaluator(QETEvaluator):

    def __init__(self, qc: QuantumCircuit, **kwargs):
        self._transformed_circuit = self.transform(qc)

        super().__init__(
            qc=self._transformed_circuit.copy(),
            optimization_level=0,
        )

    def transform(self, circuit: QuantumCircuit) -> QuantumCircuit:
        manager = PassManager([
            Optimize1qGatesDecomposition(basis=["p", "u"])
        ])
        return manager.run(circuit.copy())

    def get_transformed_circuit(self) -> QuantumCircuit:
        return self._transformed_circuit

    @staticmethod
    def get_identifier() -> str:
        return "opt1q_decomp"


class Optimize1qGatesSimpleCommutationEvaluator(QETEvaluator):

    def __init__(self, qc: QuantumCircuit, **kwargs):
        self._transformed_circuit = self.transform(qc)

        super().__init__(
            qc=self._transformed_circuit.copy(),
            optimization_level=0,
        )

    def transform(self, circuit: QuantumCircuit) -> QuantumCircuit:
        manager = PassManager([
            Optimize1qGatesSimpleCommutation(
                basis=["p", "u"],
                run_to_completion=True,
            )
        ])
        return manager.run(circuit.copy())

    def get_transformed_circuit(self) -> QuantumCircuit:
        return self._transformed_circuit

    @staticmethod
    def get_identifier() -> str:
        return "opt1q_commute"

class CommutativeInverseCancellationEvaluator(QETEvaluator):

    def __init__(self, qc: QuantumCircuit, **kwargs):
        self._transformed_circuit = self.transform(qc)

        super().__init__(
            qc=self._transformed_circuit.copy(),
            optimization_level=0,
        )

    def transform(self, circuit: QuantumCircuit) -> QuantumCircuit:
        manager = PassManager([
            CommutativeInverseCancellation()
        ])
        return manager.run(circuit.copy())

    def get_transformed_circuit(self) -> QuantumCircuit:
        return self._transformed_circuit

    @staticmethod
    def get_identifier() -> str:
        return "comm_inverse"


class OptimizeCliffordsEvaluator(QETEvaluator):

    def __init__(self, qc: QuantumCircuit, **kwargs):
        self._transformed_circuit = self.transform(qc)

        super().__init__(
            qc=self._transformed_circuit.copy(),
            optimization_level=0,
        )

    def transform(self, circuit: QuantumCircuit) -> QuantumCircuit:
        manager = PassManager([
            OptimizeCliffords()
        ])
        return manager.run(circuit.copy())

    def get_transformed_circuit(self) -> QuantumCircuit:
        return self._transformed_circuit

    @staticmethod
    def get_identifier() -> str:
        return "opt_cliffords"



class OptimizeCliffordTEvaluator(QETEvaluator):

    def __init__(self, qc: QuantumCircuit, **kwargs):
        self._transformed_circuit = self.transform(qc)

        super().__init__(
            qc=self._transformed_circuit.copy(),
            optimization_level=0,
        )

    def transform(self, circuit: QuantumCircuit) -> QuantumCircuit:
        manager = PassManager([OptimizeCliffordT()])
        return manager.run(circuit.copy())

    def get_transformed_circuit(self) -> QuantumCircuit:
        return self._transformed_circuit

    @staticmethod
    def get_identifier() -> str:
        return "opt_clifford_t"


class Split2QUnitariesEvaluator(QETEvaluator):

    def __init__(self, qc: QuantumCircuit, **kwargs):
        self._transformed_circuit = self.transform(qc)

        super().__init__(
            qc=self._transformed_circuit.copy(),
            optimization_level=0,
        )

    def transform(self, circuit: QuantumCircuit) -> QuantumCircuit:
        manager = PassManager([
            Split2QUnitaries(
                fidelity=1.0 - 1e-16,
                split_swap=False,
            )
        ])
        return manager.run(circuit.copy())

    def get_transformed_circuit(self) -> QuantumCircuit:
        return self._transformed_circuit

    @staticmethod
    def get_identifier() -> str:
        return "split_2q"


class TwoQubitPeepholeEvaluator(QETEvaluator):

    def __init__(self, qc: QuantumCircuit, **kwargs):
        self._transformed_circuit = self.transform(qc)

        super().__init__(
            qc=self._transformed_circuit.copy(),
            optimization_level=0,
        )

    def transform(self, circuit: QuantumCircuit) -> QuantumCircuit:
        n = circuit.num_qubits

        if n < 2:
            logging.info(
                "TwoQubitPeephole: no two-qubit block possible; "
                "returning circuit unchanged"
            )
            return circuit.copy()

        target = Target(num_qubits=n)

        target.add_instruction(
            UGate(
                Parameter("theta"),
                Parameter("phi"),
                Parameter("lam"),
            ),
            {
                (q,): InstructionProperties(error=0.0)
                for q in range(n)
            },
        )

        target.add_instruction(
            CXGate(),
            {
                (control, target_qubit): InstructionProperties(error=0.0)
                for control in range(n)
                for target_qubit in range(n)
                if control != target_qubit
            },
        )

        manager = PassManager([
            TwoQubitPeepholeOptimization(
                target=target,
                approximation_degree=1.0,
            )
        ])

        return manager.run(circuit.copy())

    def get_transformed_circuit(self) -> QuantumCircuit:
        return self._transformed_circuit

    @staticmethod
    def get_identifier() -> str:
        return "twoq_peephole"


class CommutativeOptimizationEvaluator(QETEvaluator):

    def __init__(self, qc: QuantumCircuit, **kwargs):
        self._transformed_circuit = self.transform(qc)

        super().__init__(
            qc=self._transformed_circuit.copy(),
            optimization_level=0,
        )

    def transform(self, circuit: QuantumCircuit) -> QuantumCircuit:
        manager = PassManager([
            CommutativeOptimization(
                approximation_degree=1.0,
            )
        ])
        return manager.run(circuit.copy())

    def get_transformed_circuit(self) -> QuantumCircuit:
        return self._transformed_circuit

    @staticmethod
    def get_identifier() -> str:
        return "comm_opt"