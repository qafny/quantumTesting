from abc import abstractmethod, ABC
from typing import List
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter, Gate
from qiskit.circuit.library import RZGate, C3XGate, C4XGate, XGate


class GateSetBasis:

    def __init__(self, basis: List[str]):
        self.basis: List[str] = basis
        self.custom_gate_definitions: List[Gate] = []

    def add_custom_gate(self, gate: Gate):
        self.custom_gate_definitions.append(gate)

    def get_custom_gate_definitions(self):
        return self.custom_gate_definitions


class QiskitBasis(GateSetBasis):

    def __init__(self):
        super(QiskitBasis).__init__(basis = ["h", "x", "rz", "cx", "crz", "ccx", "ccrz", "cccx", "cccrz", "cccx", "ccccrz", "cccccx", "cccccrz"])

        self.add_custom_gates()

    def add_custom_gates(self):
        self.add_ccrz_gate()

        self.add_cccx_gate()
        self.add_cccrz_gate()

        self.add_ccccx_gate()
        self.add_ccccrz_gate()

        self.add_cccccx_gate()
        self.add_cccccrz_gate()

    def add_ccrz_gate(self):
        qc = QuantumCircuit(3, name = "ccrz")
        phi = Parameter("phi")
        ccrz_gate = RZGate(phi).control(2)
        qc.append(ccrz_gate, [0, 1, 2])

        gate = qc.to_gate()
        self.add_custom_gate(gate)

    def add_cccx_gate(self):
        qc = QuantumCircuit(4, name = "cccx")
        qc.append(C3XGate(), [0, 1, 2, 3])

        gate = qc.to_gate()
        self.add_custom_gate(gate)

    def add_cccrz_gate(self):
        qc = QuantumCircuit(4, name = "cccrz")
        phi = Parameter("phi")
        cccrz_gate = RZGate(phi).control(3)
        qc.append(cccrz_gate, [0, 1, 2, 3])

        gate = qc.to_gate()
        self.add_custom_gate(gate)

    def add_ccccx_gate(self):
        qc = QuantumCircuit(5, name = "ccccx")
        qc.append(C4XGate(), [0, 1, 2, 3, 4])

        gate = qc.to_gate()
        self.add_custom_gate(gate)

    def add_ccccrz_gate(self):
        qc = QuantumCircuit(5, name = "ccccrz")
        phi = Parameter("phi")
        ccccrz_gate = RZGate(phi).control(4)
        qc.append(ccccrz_gate, [0, 1, 2, 3, 4])

        gate = qc.to_gate()
        self.add_custom_gate(gate)

    def add_cccccx_gate(self):
        qc = QuantumCircuit(6, name = "cccccx")
        cccccx_gate = XGate().control(5)
        qc.append(cccccx_gate, [0, 1, 2, 3, 4, 5])

        gate = qc.to_gate()
        self.add_custom_gate(gate)

    def add_cccccrz_gate(self):
        qc = QuantumCircuit(6, name = "cccccrz")
        phi = Parameter("phi")
        cccccrz_gate = RZGate(phi).control(5)
        qc.append(cccccrz_gate, [0, 1, 2, 3, 4, 5])

        gate = qc.to_gate()
        self.add_custom_gate(gate)


class TSimBasisGates(GateSetBasis):

    def __init__(self):
        super(TSimBasisGates, self).__init__(basis = ["h", "s", "cx", "t"])
