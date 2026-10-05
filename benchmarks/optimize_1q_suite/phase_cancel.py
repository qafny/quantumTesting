from qiskit import QuantumCircuit

circuit = QuantumCircuit(1)

circuit.h(0)
circuit.p(0.7, 0)
circuit.p(-0.7, 0)
circuit.h(0)
