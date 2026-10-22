from typing import List, Dict, Tuple
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter, Gate, Measure
from qiskit.circuit.library import RZGate, C3XGate, C4XGate, XGate, HGate, CXGate, CRZGate, CCXGate, TGate, SGate, \
    CUGate

class GateSetBasis:

    def __init__(self, basis: List[Tuple[Gate, Dict]]):
        self.basis: List[Tuple[Gate, Dict]] = basis
        self.custom_gate_definitions: List[Tuple[Gate, Dict, str]] = []

    def get_gate_set(self):
        return self.basis

    def add_custom_gate(self, gate: Gate, props: Dict, gate_name: str):
        self.custom_gate_definitions.append((gate, props, gate_name))

    def get_custom_gate_definitions(self):
        return self.custom_gate_definitions


class RZXGatesetBasis(GateSetBasis):

    '''
    Since there are no props for the custom gates, it assumes ideal simulation. However, if we need proper
    optimization, we need to define the dict. Check here: https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.transpiler.Target#add_instruction
    [ "x", "rz", "cx", "crz", "ccx", "ccrz", "cccx", "cccrz", "cccx", "ccccrz", "cccccx", "cccccrz"]
    '''

    def __init__(self):
        super(RZXGatesetBasis, self).__init__(basis = [
            (XGate(), {None, None}),
            (RZGate(Parameter("Phi")), {None, None}),
            (CXGate(), {None, None}),
            (CRZGate(Parameter("Theta")), {None, None}),
            (CCXGate(), {None, None}),
        ])

        self.add_custom_gates()

    def add_custom_gates(self):
        self.add_ccrz_gate()

        self.add_cccrz_gate()
        self.add_cccx_gate()

        self.add_ccccx_gate()
        self.add_ccccrz_gate()

        self.add_cccccx_gate()
        self.add_cccccrz_gate()

    def add_ccrz_gate(self):
        qc = QuantumCircuit(3, name = "ccrz")
        phi = Parameter("phi")
        ccrz_gate = RZGate(phi).control(2, annotated = True)
        qc.append(ccrz_gate, [0, 1, 2])

        gate = qc.to_gate()
        self.add_custom_gate(gate, self.gate_properties["CCRZ"], "ccrz")

    def add_cccx_gate(self):
        qc = QuantumCircuit(4, name = "cccx")
        qc.append(C3XGate(), [0, 1, 2, 3])

        gate = qc.to_gate()
        self.add_custom_gate(gate, self.gate_properties["CCCX"], "cccx")

    def add_cccrz_gate(self):
        qc = QuantumCircuit(4, name = "cccrz")
        phi = Parameter("phi")
        cccrz_gate = RZGate(phi).control(3, annotated = True)
        qc.append(cccrz_gate, [0, 1, 2, 3])

        gate = qc.to_gate()
        self.add_custom_gate(gate, self.gate_properties["CCCRZ"], "cccrz")

    def add_ccccx_gate(self):
        qc = QuantumCircuit(5, name = "ccccx")
        qc.append(C4XGate(), [0, 1, 2, 3, 4])

        gate = qc.to_gate()
        self.add_custom_gate(gate, self.gate_properties["CCCCX"], "ccccx")

    def add_ccccrz_gate(self):
        qc = QuantumCircuit(5, name = "ccccrz")
        phi = Parameter("phi")
        ccccrz_gate = RZGate(phi).control(4, annotated = True)
        qc.append(ccccrz_gate, [0, 1, 2, 3, 4])

        gate = qc.to_gate()
        self.add_custom_gate(gate, self.gate_properties["CCCCRZ"], "ccccrz")

    def add_cccccx_gate(self):
        qc = QuantumCircuit(6, name = "cccccx")
        cccccx_gate = XGate().control(5, annotated = True)
        qc.append(cccccx_gate, [0, 1, 2, 3, 4, 5])

        gate = qc.to_gate()
        self.add_custom_gate(gate, self.gate_properties["CCCCCX"], "cccccx")

    def add_cccccrz_gate(self):
        qc = QuantumCircuit(6, name = "cccccrz")
        phi = Parameter("phi")
        cccccrz_gate = RZGate(phi).control(5, annotated = True)
        qc.append(cccccrz_gate, [0, 1, 2, 3, 4, 5])

        gate = qc.to_gate()
        self.add_custom_gate(gate, self.gate_properties["CCCCCRZ"], "cccccrz")


class ZRGateSetBasis(GateSetBasis):

    def __init__(self):
        super(ZRGateSetBasis, self).__init__(basis = [
            (HGate(), None),
            (CRZGate(Parameter("Theta")), None),
            (RZGate(Parameter("Phi")), None),
        ])


class CliffordGateSetBasis(GateSetBasis):

    def __init__(self):
        super(CliffordGateSetBasis, self).__init__(basis = [
            (HGate(), None),
            (SGate(), None),
            (CXGate(), None),
            (Measure(), None)
        ])


class CliffordTGateSetBasis(GateSetBasis):

    def __init__(self):
        super(CliffordTGateSetBasis, self).__init__(basis = [
            (HGate(), None),
            (SGate(), None),
            (CXGate(), None),
            (TGate(), None),
            (Measure(), None)
        ])
