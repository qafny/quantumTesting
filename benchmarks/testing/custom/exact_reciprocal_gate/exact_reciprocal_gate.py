from qiskit import QuantumCircuit
from qiskit.circuit.library import ExactReciprocalGate


qc = QuantumCircuit(5,5)
linAmplitudeGate = ExactReciprocalGate(num_state_qubits=3, scaling=4.0)
qc.append(linAmplitudeGate, [0,1,2,3])
