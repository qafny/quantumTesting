import cmath
import math
from typing import Dict
from qetast.nodes import QXH, QXRZ, QXX, QXCU
from qetast.program import QETASTVisitor
from qetast.values import CoqNVal, CoqYVal, exchange

def merge_aux(x: tuple[float,dict], y:list[tuple[float,dict]]):

    test = False
    tmp = []
    for (q,p) in y:
        if x[1] == p:
            test = True
            tmp.append((x[0] + q,p))
        else:
            tmp.append((q,p))
    return test,tmp

def merge(y:list[tuple[float,dict]]):

    re = []
    while len(y) > 0:
        value = y.pop(0)
        test,y = merge_aux(value, y)
        if not test:
            re.append(value)
    return re


class QETSimulator(QETASTVisitor):

    def __init__(self, state: list[tuple[complex, dict]]):
        self.state = state

    def visitH(self, node: QXH):
        idx = node.qubit()

        tmp = []
        for (x,y) in self.state:
            if y.get(idx):
                tmp.append((- math.sqrt(2)/2 * x,y.update({idx:True})))
                tmp.append((math.sqrt(2)/2 * x,y.update({idx:False})))
            else:
                tmp.append((math.sqrt(2)/2 * x,y.update({idx:True})))
                tmp.append((math.sqrt(2)/2 * x,y.update({idx:False})))

        tmp = merge(tmp)
        self.state = merge(tmp)
        return True

    def visitX(self, node: QXX):
        idx = node.qubit()
        self.state = [(x,y.update({idx: not y.get(idx)})) for (x,y) in self.state]

        return True

    def visitRZ(self, node: QXRZ):
        idx = node.qubit()
        phase = node.phase().value()

        tmp = []
        for (x,y) in self.state:
            if y.get(idx):
                tmp.append((x*cmath.exp(1j * phase), y))
            else:
                tmp.append((x,y))
        self.state = tmp

        return True

    def visitCU(self, node: QXCU):
        idx = node.qubit()

        re = []
        it = self.state
        for i in range(it):
            if it[i][1].get(idx):
                tmp = self.state
                self.state = [it[i]]
                node.program().accept(self)
                re.append(self.state)
                self.state = tmp
            else:
                re.append(it[i])

        self.state = re

        return True
