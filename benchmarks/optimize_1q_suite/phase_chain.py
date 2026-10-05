from qiskit import QuantumCircuit

circuit = QuantumCircuit(1)

circuit.h(0)
circuit.p(0.1, 0)
circuit.p(0.2, 0)
circuit.p(-0.4, 0)
circuit.p(0.6, 0)
circuit.h(0)
