from typing import List, Dict


def gen_qubit_states(states: List[List[bool]], cstate: List[bool], idx: int):
    if idx == len(cstate) - 1:
        cstate[idx] = False
        states.append(cstate[:])

        cstate[idx] = True
        states.append(cstate[:])
    else:
        cstate[idx] = False
        gen_qubit_states(states, cstate, idx + 1)

        cstate[idx] = True
        gen_qubit_states(states, cstate, idx + 1)


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
