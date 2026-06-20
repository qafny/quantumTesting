import math
from qiskit import QuantumCircuit
from qetast.nodes import QXRoot, QXH, QXX, QXRZ, QXCU, QXMeasure
from qetast.program import QETASTVisitor


class QuantumCircuitPrinter(QETASTVisitor):

    def __init__(self):
        self.qc: QuantumCircuit = None

        self.cbit_count = 0

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
            if node.phase().value() == math.pi:
                self.qc.z(int(node.qubit()))
            elif node.phase().value() == math.pi / 2:
                self.qc.s(int(node.qubit()))
            elif node.phase().value() == - math.pi / 2:
                self.qc.sdg(int(node.qubit()))
            elif node.phase().value() == math.pi / 4:
                self.qc.t(int(node.qubit()))
            elif node.phase().value() == - math.pi / 4:
                self.qc.tdg(int(node.qubit()))
            else:
                _phi = node.phase().value()
                self.qc.rz(phi=_phi, qubit=int(node.qubit()))
        else:
            # TODO: Add support for more than two control gates (qiskit does not support beyond ccG); G = Gate
            kwargs = self.prepare_controlled_gate_kwargs(node.qubit())

            if node.phase().value() == math.pi:
                getattr(self.qc, self.c["prefix"] + "z")(**kwargs)
            elif node.phase().value() == math.pi / 2:
                getattr(self.qc, self.c["prefix"] + "s")(**kwargs)
            elif node.phase().value() == - math.pi / 2:
                getattr(self.qc, self.c["prefix"] + "sdg")(**kwargs)
            else:
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

    def visitMeasure(self, node: QXMeasure):
        self.qc.measure(int(node.qubit()), self.cbit_count)
        self.cbit_count += 1

        return True


class TSimPrinter(QETASTVisitor):

    def __init__(self):
        self.tsim_program = ""
        self.c_qubit = ""

    def visitRoot(self, node: QXRoot):
        retval = super(TSimPrinter, self).visitRoot(node)
        for qubit in node.qubits():
            self.tsim_program += f"I {qubit.ID()}\n"

        return retval

    def visitH(self, node: QXH):
        self.tsim_program += f"H {node.qubit()}\n"
        return True

    def visitX(self, node: QXX):
        if self.c_qubit != "":
            self.tsim_program += f"CNOT {self.c_qubit} {node.qubit()}\n"

        return True

    def visitRZ(self, node: QXRZ):
        if node.phase().value() == math.pi / 2:
            self.tsim_program += f"S {node.qubit()}\n"
        elif node.phase().value() == math.pi / 4:
            self.tsim_program += f"T {node.qubit()}\n"

        return True

    def visitCU(self, node: QXCU):
        self.c_qubit = node.qubit()
        retval = node.program().accept(self)
        self.c_qubit = ""

        return retval

    def visitMeasure(self, node: QXMeasure):
        self.tsim_program += f"M {node.qubit()}\n"
