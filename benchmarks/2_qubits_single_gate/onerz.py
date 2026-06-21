import math
from qiskit import QuantumCircuit


qc = QuantumCircuit(2)
qc.rz(qubit=0, phi=math.pi)
