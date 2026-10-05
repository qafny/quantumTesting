from qiskit import QuantumCircuit

circuit = QuantumCircuit(2)

circuit.h(0)
circuit.h(1)
circuit.p(0.2, 1)
circuit.cx(0, 1)
circuit.p(0.3, 1)
circuit.h(0)
circuit.h(1)
