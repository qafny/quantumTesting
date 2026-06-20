import math
from typing import List
from qiskit import QuantumCircuit
from qiskit.circuit import CircuitInstruction
from qetast.nodes import QXQubit, QXH, QXX, QXConstant, QXRZ, QXCU, QXProgram, QXRoot, QXMeasure


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
                return [QXRZ(qubits[0].ID(), QXConstant(math.pi))]
            case "s":
                return [QXRZ(qubits[0].ID(), QXConstant(math.pi / 2))]
            case "sdg":
                return [QXRZ(qubits[0].ID(), QXConstant(-math.pi / 2))]
            case "t":
                return [QXRZ(qubits[0].ID(), QXConstant(math.pi / 4))]
            case "tdg":
                return [QXRZ(qubits[0].ID(), QXConstant(-math.pi / 4))]
            case "rz":
                return [QXRZ(qubits[0].ID(), QXConstant(params[0]))]
            case "cx":
                return [
                    QXCU(qubits[0].ID(), QXProgram([
                        QXX(qubits[1].ID())
                    ]))
                ]
            case "crz":
                return [
                    QXCU(qubits[0].ID(), QXProgram([
                        QXRZ(qubits[1].ID(), QXConstant(params[0])),
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
                            QXRZ(qubits[2].ID(), QXConstant(params[0])),
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
                                QXRZ(qubits[3].ID(), QXConstant(params[0])),
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
                                    QXRZ(qubits[4].ID(), QXConstant(params[0])),
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
                                        QXRZ(qubits[5].ID(), QXConstant(params[0])),
                                    ]))
                                ]))
                            ]))
                        ]))
                    ]))
                ]
            case "measure":
                # TODO: Is it the same to measure qubits individually and measure them together in qiskit?
                return [
                    QXMeasure(qubit.ID()) for qubit in qubits
                ]

        return None

    def parse(self):
        self.setup_qubits()

        exps = []
        for instruction in self.qc.data:
            exps.extend(self.parse_instruction(instruction))

        qubits = [qubit for _, qubit in self.qc_mapping.items()]

        global_phase = self.qc.global_phase

        return QXRoot(QXProgram(exps), qubits, global_phase)
