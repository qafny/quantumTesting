"""
This file contains a visitor which traverses a Qiskit Quantum Circuit and 
converts it into the format required for "XMLProgrammer.py".
"""

import math
import qiskit
from qiskit import transpile
from qiskit import QuantumCircuit
from qiskit.converters import circuit_to_dag
from qiskit.dagcircuit import DAGInNode, DAGOpNode, DAGNode, DAGOutNode
from qiskit.visualization import dag_drawer
import graphviz
import os
import sys
from qiskit.circuit.library.arithmetic import FullAdderGate

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# current_dir = os.path.dirname(os.path.abspath(__file__))
# sys.path.append(os.path.join(current_dir, "PQASM"))

from AST_Scripts.XMLProgrammer import QXProgram, QXQID, QXCU, QXX, QXH, QXRZ, QXRY, QXVexp, QXNum
from AST_Scripts.XMLPrinter import XMLPrinter

# Ensure graphviz is in the PATH (for dag drawing)
os.environ["PATH"] += os.pathsep + r"C:\Program Files\Graphviz\bin"

# ------------------------- DAG TO XMLPROGRAMMER -------------------------------

supportedGates = ['cx','h','s','t']
ignoredGates = ['measure']

def decomposeToGates(qc, optimiseCircuit, gateSetToUse):
    # Unoptimised circuits are more readable.
    if optimiseCircuit:
        return transpile(qc, basis_gates=gateSetToUse + ignoredGates)
    return transpile(qc, basis_gates=gateSetToUse + ignoredGates, optimization_level=0)
   
class QCtoXMLProgrammer:
    def __init__(self):
        self.dag = None

    def startVisit(
        self,
        qc,
        circuitName=None,
        optimiseCircuit=False,
        showDecomposedCircuit=True,
        showInputCircuit=True,
        emit_xml=True,
        gateSetToUse = supportedGates
    ):
        print()
        if circuitName is not None:
            print("------------------- COMPILING CIRCUIT: " + str(circuitName) + " -------------------")
        else:
            print("------------------- COMPILING CIRCUIT: " + "[Name Unknown]" + " -------------------")

        
        if showInputCircuit:
            print("Input Circuit:")
            print(qc.draw())
            print()


        qc = decomposeToGates(qc, optimiseCircuit, gateSetToUse)
        if showDecomposedCircuit:
            print("Decomposed Circuit:")
            print(qc.draw())

        # Map Qiskit qubits → XMLProgrammer position indices
        self.XMLQubits = dict()
        for i, qubit in enumerate(qc.qubits):
            self.XMLQubits[qubit] = QXNum(i)

        # Iterate directly over qc.data — Qiskit already guarantees topological
        # order after transpile(), so no DAG re-traversal is needed.
        self.expList = []
        for instr in qc.data:
            self.instrToXMLProgrammer(instr, qc)

        self.program = QXProgram(self.expList)
        print("Extracted QXProgram (AST):")
        print(self.program)

        if emit_xml:
            xml = XMLPrinter()
            xml.visitProgram(self.program)
            print("XML Representation:")
            print(xml.xml_output)
        else:
            print("XML emission skipped; AST is available via return value.")

        print("------------------------------------------------------------")
        return self.program

    def instrToXMLProgrammer(self, instr, qc):
        """Translate one CircuitInstruction from qc.data into XMLProgrammer AST nodes."""
        name   = instr.operation.name
        params = instr.operation.params
        qubits = [self.XMLQubits[q] for q in instr.qubits]
        exps   = []

        # Single-qubit gates
        if name == "h":
            exps.append(QXH("test", qubits[0]))
        elif name == "x":
            exps.append(QXX("test", qubits[0]))
        elif name == "y":
            exps.append(QXRY("test", qubits[0], QXNum(90)))
        elif name == "z":
            exps.append(QXRZ("test", qubits[0], QXNum(180)))

        # Fractional phase shifts (S, T):
        elif name == "s":
            exps.append(QXRZ("test", qubits[0], QXNum(90)))
        elif name == "sdg":
            exps.append(QXRZ("test", qubits[0], QXNum(-90)))
        elif name == "t":
            exps.append(QXRZ("test", qubits[0], QXNum(45)))
        elif name == "tdg":
            exps.append(QXRZ("test", qubits[0], QXNum(-45)))

        # General rotations
        elif name == "ry":
            exps.append(QXRY("test", qubits[0], QXNum(params[0] * 180 / math.pi)))
        elif name == "rz":
            exps.append(QXRZ("test", qubits[0], QXNum(params[0] * 180 / math.pi)))

        # Universal single-qubit gate U(a,b,c) = RZ(a) RY(b) RZ(c)
        elif name == "u":
            exps.append(QXRZ("test", qubits[0], QXNum(params[0] * 180 / math.pi)))
            exps.append(QXRY("test", qubits[0], QXNum(params[1] * 180 / math.pi)))
            exps.append(QXRZ("test", qubits[0], QXNum(params[2] * 180 / math.pi)))

        # Controlled operations:
        # cx  → CU(ctrl,  { X(target) })
        # ccx → CU(ctrl0, { CU(ctrl1, { X(target) }) })  — Toffoli as nested CU
        # cz  → CU(ctrl,  { RZ(target, 180) })
        # crz → CU(ctrl,  { RZ(target, angle) })
        elif name == "cx":
            exps.append(QXCU("test", qubits[0], QXProgram([QXX("test", qubits[1])])))
        elif name == "ccx":
            exps.append(QXCU("test", qubits[0], QXProgram([
                QXCU("test", qubits[1], QXProgram([QXX("test", qubits[2])]))
            ])))
        elif name == "cz":
            exps.append(QXCU("test", qubits[0], QXProgram([QXRZ("test", qubits[1], QXNum(180))])))
        elif name == "crz":
            exps.append(QXCU("test", qubits[0], QXProgram([
                QXRZ("test", qubits[1], QXNum(params[0] * 180 / math.pi))
            ])))

        elif name in ignoredGates:
            pass

        else:
            print("Warning: Unrecognized operation", name)

        # TODO: Write post parser processors for this
        # Validate that any rotation angle is a concrete number (not an unbound parameter)
        for exp in exps:
            if type(exp) in [QXRY, QXRZ]:
                try:
                    float(exp.num().num())
                except Exception as e:
                    raise TypeError(
                        f"Unbound parameter in gate '{name}': angle={exp.angle}. "
                        "Bind all parameters before compiling to XMLProgrammer."
                    )
            self.expList.append(exp)
                