import cmath
import logging
import math
from typing import Dict
import numpy as np
from qiskit import QuantumCircuit
from tsim import Circuit
from evaluators.base import BaseEvaluator
from evaluators.basis import CliffordTGateSetBasis
from qetast.printers import TSimPrinter
import evaluators.utils as eval_utils


class TSimEvaluator(BaseEvaluator):

    def __init__(self, qc: QuantumCircuit, optimization_level: int):
        logging.info("Initializing TSimEvaluator")
        super(TSimEvaluator, self).__init__(qc, CliffordTGateSetBasis(), optimization_level)
        self.u: np.ndarray = None

        logging.info("Building up the Unitary for TSim")
        self.setup_unitary()
        logging.info("Finished Building up the Unitary for TSim")

        logging.info("Finished Initializing TSimEvaluator")

    @staticmethod
    def get_identifier():
        return "tsim"

    def setup_unitary(self):
        logging.info("Converting to a TSim Program")
        tsim_printer = TSimPrinter()
        tsim_printer.visitRoot(self.get_circuit_ast())
        logging.info("Finished Converting to a TSim Program")

        tsim_src = tsim_printer.tsim_program

        ## TODO: Maybe find how to add global phase to TSim program?
        phi = self.get_circuit_ast().global_phase()

        logging.info("Transforming to the Unitary")
        circuit = Circuit(tsim_src)
        self.u = cmath.exp(1j * phi) * circuit.to_matrix()
        logging.info("Finished Transforming to the Unitary")

    def evaluate(self, ins: Dict[str, bool]):
        logging.info("Evaluating using TSimEvaluator")

        tmp = [0] * len(ins)
        for idx, bval in ins.items():
            tmp[int(idx)] = bval

        arr_in = None
        for bval in tmp:
            if bval:
                if arr_in is None:
                    arr_in = np.array([0, 1])
                else:
                    arr_in = np.kron(arr_in, [0, 1])
            else:
                if arr_in is None:
                    arr_in = np.array([1, 0])
                else:
                    arr_in = np.kron(arr_in, [1, 0])

        arr_out = np.matmul(self.u, arr_in)

        state = []
        for idx, amp in np.ndenumerate(arr_out):
            amp = eval_utils.zcomplex(amp)

            # We eliminate 0 amplitude basis-kets.
            if amp == 0:
                continue

            c = int(math.log2(arr_out.shape[0]))
            frmtr_str = "{:0" + str(c) + "b}"

            sd = {}
            for i, bs in enumerate(frmtr_str.format(idx[0])):
                sd[str(i)] = True if bs == "1" else False

            state.append((amp, sd))

        logging.info("Finished Evaluating using TSimEvaluator")

        return state
