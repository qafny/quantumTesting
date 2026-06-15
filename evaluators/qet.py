from typing import Dict, List
from evaluators.base import BaseEvaluator
from qetast.nodes import QXRoot
from qetast.simulators import QETSimulator


def create_state_from_bitvals(bitvals: List):
    state = {}
    for idx in range(len(bitvals)):
        state[str(idx)] = bitvals[idx]

    return state


def generate_basis_states(bitvals: list, bstates: List[Dict], i: int):
    if i == len(bitvals) - 1:
        bitvals[i] = True
        bstates.append(create_state_from_bitvals(bitvals))

        bitvals[i] = False
        bstates.append(create_state_from_bitvals(bitvals))
    else:
        bitvals[i] = True
        generate_basis_states(bitvals, bstates, i + 1)

        bitvals[i] = False
        generate_basis_states(bitvals, bstates, i + 1)


def get_system_state_from_qubits(qubit_states: Dict[str, bool]):
    system_state = [(1 + 0j, qubit_states)]

    basis_states = []
    generate_basis_states([False] * len(qubit_states), basis_states, 0)
    for basis_state in basis_states:
        if basis_state != qubit_states:
            system_state.append((0 + 0j, basis_state))

    return system_state


class QETEvaluator(BaseEvaluator):

    def __init__(self, root: QXRoot):
        super(QETEvaluator, self).__init__()
        self.root = root

    def evaluate(self, ins: Dict[str, bool]):
        initial_state = get_system_state_from_qubits(ins)

        simulator = QETSimulator(initial_state)
        simulator.visitRoot(self.root)

        return simulator.state
