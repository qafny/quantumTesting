from typing import Dict
from evaluators.base import BaseEvaluator
from qetast.markers import PrefixedHadamardGatesMarker, SuffixedHadamardGatesMarker, AllHadamardGatesMarker
from qetast.nodes import QXRoot
from qetast.processors import MarkedNodeEliminator


class QETEvaluator(BaseEvaluator):

    PRE_MARKERS = [
        PrefixedHadamardGatesMarker(),
        SuffixedHadamardGatesMarker(),
    ]

    PRE_ELIMINATORS = [
        MarkedNodeEliminator(),
    ]

    def __init__(self):
        # TODO: Save evaluation results and such
        pass

    def apply_pre_markers(self, root: QXRoot):
        for marker in self.PRE_MARKERS:
            root = marker.visitRoot(root)

        return root

    def apply_pre_eliminators(self, root: QXRoot):
        for eliminator in self.PRE_ELIMINATORS:
            root = eliminator.visitRoot(root)

        return root

    def apply_mark_middle_hadamards(self, root: QXRoot):
        ah_marker = AllHadamardGatesMarker()
        return ah_marker.visitRoot(root)

    def evaluate(self, root: QXRoot, state0: Dict, env0: Dict):
        uroot = self.apply_pre_markers(root)
        uroot = self.apply_pre_eliminators(uroot)

        # Partitioned Evaluation
        uroot = self.apply_mark_middle_hadamards(uroot)
