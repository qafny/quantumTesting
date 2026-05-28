import math
from typing import Dict
from qetast.nodes import QXH, QXRZ, QXX, QXCU
from qetast.program import QETASTVisitor
from qetast.values import CoqNVal, CoqYVal, exchange


class QETSimulator(QETASTVisitor):

    def __init__(self, state: Dict, environment: Dict):
        self.state = state
        self.environment = environment

    def visitH(self, node: QXH):
        idx = node.qubit()
        x = self.state.get(idx)

        if isinstance(x, CoqNVal):
            if x:
                self.state[idx] = CoqYVal([(math.sqrt(2)/2, 0)],[(-math.sqrt(2)/2, 0)])
            else:
                self.state[idx] = CoqYVal([(math.sqrt(2)/2, 0)],[(math.sqrt(2)/2, 0)])
        elif isinstance(x, CoqYVal):
            self.state[idx].addH()

        self.state[idx] = self.state[idx].simpRy(x)

        return True

    def visitX(self, node: QXX):
        idx = node.qubit()
        x = self.state.get(idx)

        exchange(x)

        return True

    def visitRZ(self, node: QXRZ):
        idx = node.qubit()
        x = self.state.get(idx)
        phase = node.phase().value()

        if isinstance(x, CoqNVal):
            x.setPhase(phase)
        elif isinstance(x, CoqYVal):
            x.applyMult(phase)
        else:
            return False

        return True

    def visitCU(self, node: QXCU):
        idx = node.qubit()
        x = self.state.get(idx)

        if x.getBit():
            return node.program().accept(self)
        else:
            return False
