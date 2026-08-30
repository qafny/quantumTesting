from compiler_testing.reporting.result_models import BasisSet


CONTROLLED_UNITARY_GATE_NAMES = {
    "cx",
    "ccx",
    "mcx",
    "cu",
    "cu1",
    "cu3",
    "cp",
    "crx",
    "cry",
    "crz",
}


BASIS_SET_1 = BasisSet(
    name="basis_set_1_h_rz_x_controlled_u",
    exact_gates={
        "h",
        "rz",
        "x",
    },
    allow_controlled_unitary=True,
    controlled_gate_names=CONTROLLED_UNITARY_GATE_NAMES,
)


BASIS_SET_2 = BasisSet(
    name="basis_set_2_h_s_cx",
    exact_gates={
        "h",
        "s",
        "cx",
    },
    allow_controlled_unitary=False,
)


ALL_BASIS_SETS = {
    BASIS_SET_1.name: BASIS_SET_1,
    BASIS_SET_2.name: BASIS_SET_2,
}