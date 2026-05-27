from qiskit import QuantumCircuit


qc = QuantumCircuit(4)
qc.cry(0.1, 0, 3)
qc.ry(0.5, 3)
