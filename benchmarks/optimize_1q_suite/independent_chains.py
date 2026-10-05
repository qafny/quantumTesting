from qiskit import QuantumCircuit

circuit = QuantumCircuit(2)

circuit.h(0)
circuit.h(1)
circuit.p(0.2, 0)
circuit.p(0.4, 1)
circuit.p(0.3, 0)
circuit.p(-0.1, 1)
circuit.h(0)
circuit.h(1)
