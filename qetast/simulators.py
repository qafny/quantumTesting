import cmath
import copy
import math
from typing import Dict
from qetast.nodes import QXH, QXRZ, QXX, QXCU
from qetast.program import QETASTVisitor
from qetast.values import CoqNVal, CoqYVal, exchange


def merge_aux(x: tuple[complex, dict], y: list[tuple[complex, dict]]):
    test = False
    tmp = []
    for (q, p) in y:
        if x[1] == p:
            test = True
            tmp.append((x[0] + q, p))
        else:
            tmp.append((q, p))

    return test, tmp


def merge(y: list[tuple[complex, dict]]):
    re = []
    while len(y) > 0:
        value = y.pop(0)
        test, y = merge_aux(value, y)
        if not test:
            re.append(value)
    return re


def cupdate_dict(d: dict, u: dict) -> dict:
    ud = copy.deepcopy(d)
    return ud | u


class QETSimulator(QETASTVisitor):

    def __init__(self, state: list[tuple[complex, dict]]):
        self.state = state

    def visitH(self, node: QXH):
        idx = node.qubit()

        tmp = []
        for (x, y) in self.state:
            if y.get(idx):
                tmp.append((- math.sqrt(2)/2 * x, cupdate_dict(y, {idx: True})))
                tmp.append((math.sqrt(2)/2 * x, cupdate_dict(y, {idx: False})))
            else:
                tmp.append((math.sqrt(2)/2 * x, cupdate_dict(y, {idx: True})))
                tmp.append((math.sqrt(2)/2 * x, cupdate_dict(y, {idx: False})))

        tmp = merge(tmp)
        self.state = tmp
        return True

    def visitX(self, node: QXX):
        idx = node.qubit()
        self.state = [(x, cupdate_dict(y, {idx: not y.get(idx)})) for (x,y) in self.state]

        return True

    def visitRZ(self, node: QXRZ):
        idx = node.qubit()
        phase = node.phase().value()

        tmp = []
        for (x, y) in self.state:
            if y.get(idx):
                tmp.append((x * cmath.exp(1j * phase), y))
            else:
                tmp.append((x, y))

        self.state = tmp

        return True

    def visitCU(self, node: QXCU):
        idx = node.qubit()

        re = []
        it = self.state
        for i in range(len(it)):
            if it[i][1].get(idx):
                tmp = self.state
                self.state = [it[i]]
                node.program().accept(self)
                re.extend(self.state)
                self.state = tmp
            else:
                re.append(it[i])

        self.state = re

        return True
