from qiskit import QuantumCircuit

circuit = QuantumCircuit(1)

circuit.u(0.4, 0.2, -0.3, 0)
circuit.u(-0.7, 0.5, 0.8, 0)
circuit.u(0.6, -0.4, 0.1, 0)
