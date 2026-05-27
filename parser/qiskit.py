import math
from typing import List
from qiskit import QuantumCircuit
from qiskit.circuit import CircuitInstruction
from qetast.nodes import QXQubit, QXH, QXX, QXConstant, QXRZ, QXCU, QXProgram, QXRoot


class QiskitASTParser:

    def __init__(self, qc: QuantumCircuit):
        self.qc: QuantumCircuit = qc
        self.qc_mapping = dict()

    def setup_qubits(self):
        for i, qubit in enumerate(self.qc.qubits):
            self.qc_mapping[qubit] = QXQubit(str(i))

    def parse_instruction(self, instruction: CircuitInstruction):
        gate: str = instruction.operation.name
        params: List = instruction.operation.params
        qubits: List[QXQubit] = [self.qc_mapping[qubit] for qubit in instruction.qubits]

        match gate:
            case "h":
                return [QXH(qubits[0].ID())]
            case "x":
                return [QXX(qubits[0].ID())]
            case "z":
                return [QXRZ(qubits[0].ID(), QXConstant(180))]
            case "s":
                return [QXRZ(qubits[0].ID(), QXConstant(90))]
            case "sdg":
                return [QXRZ(qubits[0].ID(), QXConstant(-90))]
            case "t":
                return [QXRZ(qubits[0].ID(), QXConstant(45))]
            case "tdg":
                return [QXRZ(qubits[0].ID(), QXConstant(-45))]
            case "rz":
                return [QXRZ(qubits[0].ID(), QXConstant(params[0] * 180 / math.pi))]
            case "cx":
                return [
                    QXCU(qubits[0].ID(), QXProgram([
                        QXX(qubits[1].ID())
                    ]))
                ]
            case "crz":
                return [
                    QXCU(qubits[0].ID(), QXProgram([
                        QXRZ(qubits[1].ID(), QXConstant(params[0] * 180 / math.pi)),
                    ]))
                ]
            case "ccx":
                return [
                    QXCU(qubits[0].ID(), QXProgram([
                        QXCU(qubits[1].ID(), QXProgram([
                            QXX(qubits[2].ID())
                        ]))
                    ]))
                ]
            case "ccrz":
                return [
                    QXCU(qubits[0].ID(), QXProgram([
                        QXCU(qubits[1].ID(), QXProgram([
                            QXRZ(qubits[2].ID(), QXConstant(params[0] * 180 / math.pi)),
                        ]))
                    ]))
                ]
            case "cccx":
                return [
                    QXCU(qubits[0].ID(), QXProgram([
                        QXCU(qubits[1].ID(), QXProgram([
                            QXCU(qubits[2].ID(), QXProgram([
                                QXX(qubits[3].ID()),
                            ]))
                        ]))
                    ]))
                ]
            case "cccrz":
                return [
                    QXCU(qubits[0].ID(), QXProgram([
                        QXCU(qubits[1].ID(), QXProgram([
                            QXCU(qubits[2].ID(), QXProgram([
                                QXRZ(qubits[3].ID(), QXConstant(params[0] * 180 / math.pi)),
                            ]))
                        ]))
                    ]))
                ]
            case "ccccx":
                return [
                    QXCU(qubits[0].ID(), QXProgram([
                        QXCU(qubits[1].ID(), QXProgram([
                            QXCU(qubits[2].ID(), QXProgram([
                                QXCU(qubits[3].ID(), QXProgram([
                                    QXX(qubits[4].ID()),
                                ]))
                            ]))
                        ]))
                    ]))
                ]
            case "ccccrz":
                return [
                    QXCU(qubits[0].ID(), QXProgram([
                        QXCU(qubits[1].ID(), QXProgram([
                            QXCU(qubits[2].ID(), QXProgram([
                                QXCU(qubits[3].ID(), QXProgram([
                                    QXRZ(qubits[4].ID(), QXConstant(params[0] * 180 / math.pi)),
                                ]))
                            ]))
                        ]))
                    ]))
                ]
            case "cccccx":
                return [
                    QXCU(qubits[0].ID(), QXProgram([
                        QXCU(qubits[1].ID(), QXProgram([
                            QXCU(qubits[2].ID(), QXProgram([
                                QXCU(qubits[3].ID(), QXProgram([
                                    QXCU(qubits[4].ID(), QXProgram([
                                        QXX(qubits[5].ID()),
                                    ]))
                                ]))
                            ]))
                        ]))
                    ]))
                ]
            case "cccccrz":
                return [
                    QXCU(qubits[0].ID(), QXProgram([
                        QXCU(qubits[1].ID(), QXProgram([
                            QXCU(qubits[2].ID(), QXProgram([
                                QXCU(qubits[3].ID(), QXProgram([
                                    QXCU(qubits[4].ID(), QXProgram([
                                        QXRZ(qubits[5].ID(), QXConstant(params[0] * 180 / math.pi)),
                                    ]))
                                ]))
                            ]))
                        ]))
                    ]))
                ]
            case "measure":
                return []

        return None

    def parse(self):
        self.setup_qubits()

        exps = []
        for instruction in self.qc.data:
            exps.extend(self.parse_instruction(instruction))

        qubits = [qubit for _, qubit in self.qc_mapping.items()]

        return QXRoot(QXProgram(exps), qubits)
