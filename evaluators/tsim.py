from tsim import Circuit
from evaluators.base import BaseEvaluator
from qetast.nodes import QXRoot
from qetast.printers import TSimPrinter


class TSimEvaluator(BaseEvaluator):

    COUNT_SHOTS = 100

    def __init__(self, evaluate_shots: int = COUNT_SHOTS):
        super(TSimEvaluator).__init__()
        self.evaluate_shots = evaluate_shots

    def evaluate(self, root: QXRoot):
        tsim_printer = TSimPrinter()
        tsim_printer.visitRoot(root)

        tsim_src = tsim_printer.tsim_program

        circuit = Circuit(tsim_src)
        sampler = circuit.compile_detector_sampler()

        return sampler.sample(self.evaluate_shots)
