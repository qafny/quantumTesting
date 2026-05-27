import math
from qiskit import QuantumCircuit
from qetast.nodes import QXRoot, QXH, QXX, QXRZ, QXCU
from qetast.program import QETASTVisitor


class QuantumCircuitPrinter(QETASTVisitor):

    def __init__(self):
        self.qc: QuantumCircuit = None

        self.c = self.c = {
            "prefix": "",
            "qubits": [],
        }

    def prepare_controlled_gate_kwargs(self, target_qubit: str):
        kwargs = {
            "target_qubit": int(target_qubit),
        }
        if len(self.c["qubits"]) > 1:
            for i in range(len(self.c["qubits"])):
                kwargs[f"control_qubit{i + 1}"] = self.c["qubits"][i]
        else:
            kwargs[f"control_qubit"] = self.c["qubits"][0]

        return kwargs

    def visitRoot(self, node: QXRoot):
        self.qc = QuantumCircuit(len(node.qubits()))
        return super(QuantumCircuitPrinter, self).visitRoot(node)

    def visitH(self, node: QXH):
        self.qc.h(int(node.qubit()))
        return True

    def visitX(self, node: QXX):
        if self.c["prefix"] == "":
            self.qc.x(int(node.qubit()))
        else:
            # TODO: Add support for more than two control gates (qiskit does not support beyond ccx)
            kwargs = self.prepare_controlled_gate_kwargs(node.qubit())
            getattr(self.qc, self.c["prefix"] + "x")(**kwargs)
        return True

    def visitRZ(self, node: QXRZ):
        if self.c["prefix"] == "":
            match node.phase().value():
                case 180:
                    self.qc.z(int(node.qubit()))
                case 90:
                    self.qc.s(int(node.qubit()))
                case -90:
                    self.qc.sdg(int(node.qubit()))
                case 45:
                    self.qc.t(int(node.qubit()))
                case -45:
                    self.qc.tdg(int(node.qubit()))
                case _:
                    _phi = node.phase().value() * math.pi / 180
                    self.qc.rz(phi=_phi, qubit=int(node.qubit()))
        else:
            # TODO: Add support for more than two control gates (qiskit does not support beyond ccG); G = Gate
            kwargs = self.prepare_controlled_gate_kwargs(node.qubit())

            match node.phase().value():
                case 180:
                    getattr(self.qc, self.c["prefix"] + "z")(**kwargs)
                case 90:
                    getattr(self.qc, self.c["prefix"] + "s")(**kwargs)
                case -90:
                    getattr(self.qc, self.c["prefix"] + "sdg")(**kwargs)
                # TODO: Check for no controlled t and tdg gates
                case _:
                    kwargs["theta"] = node.phase().value() * math.pi / 180
                    getattr(self.qc, self.c["prefix"] + "rz")(**kwargs)

        return True

    def visitCU(self, node: QXCU):
        # TODO: Find a way to detect and print U gate
        self.c["prefix"] += "c"
        self.c["qubits"].append(int(node.qubit()))
        retval = node.program().accept(self)
        self.c["prefix"] = self.c["prefix"][:-1]
        self.c["qubits"] = self.c["qubits"][:-1]

        return retval
