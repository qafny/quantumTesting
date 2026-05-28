from qetast.helpers import *


def exchange(coq_val: CoqVal):
    if isinstance(coq_val, CoqNVal):
        coq_val.setBit(not coq_val.getBit())
    if isinstance(coq_val, CoqYVal):
        coq_val.flip()


def up_h(v, rmax):
    if isinstance(v, CoqNVal):
        b = v.val
        r = v.phase
        if b:
            return CoqQVal(
                r,
                rotate(0, 1, rmax)
            )
        else:
            return CoqQVal(r, 0)
    else:
        r = v.r1
        f = v.r2
        return CoqNVal(
            2 ** max_helper(rmax, 1) <= f,
            r
        )


class CoqVal:
    pass


class CoqNVal(CoqVal):

    def __init__(self, val: bool, phase: int):
        self.val = val
        self.phase = phase

    def getBit(self):
        return self.val

    def setBit(self, b: bool):
        self.val = b

    def getPhase(self):
        return self.phase

    def setPhase(self, i: int):
        self.phase += i


class CoqQVal(CoqVal):

    def __init__(self, r1: int, r2: int, b: [bool] = None, n: int = None):
        self.r1 = r1
        self.r2 = r2
        self.n = n
        self.b = b

    def getPhase(self):
        return self.r1

    def getLocal(self):
        return self.r2

    def getRest(self):
        return self.b

    def getNum(self):
        return self.n


#first flow is the amplitude, and the second flow is the phase int ==> exp(i * pi/int)
class CoqYVal(CoqVal):

    def __init__(self, r1: list[tuple[float, int]], r2: list[tuple[float, int]]):
        self.r1 = r1
        self.r2 = r2

    def getZero(self):
        return self.r1

    def getOne(self):
        return self.r2

    def simpRy(self, a: CoqYVal):
        if not a.getZero():
            return CoqNVal([0],0)
        elif len(a.getZero()) == 1 and a.getZero()[0][0] == 0:
            return CoqNVal([0],0)
        elif not a.getOne():
            return CoqNVal([0],0)
        elif len(a.getOne()) == 1 and a.getOne()[0][0] == 0:
            return CoqNVal([0],0)
        else:
            return a

    def addY(self, r):
        if len(self.r1) == 1 and len(self.r2) == 1 and self.r1[0][1] == 0 and self.r2[0][1] == 0:
            a0, b0 = self.r1[0][0], self.r2[0][0]
            cr, sr = math.cos(math.pi * r / 90), math.sin(math.pi * r / 90)
            self.r1 = [(cr * a0 - sr * b0, 0)]
            self.r2 = [(sr * a0 + cr * b0, 0)]

    def addH(self):
        if len(self.r1) == 1 and len(self.r2) == 1 and self.r1[0][1] == 0 and self.r2[0][1] == 0:
            a0, b0 = self.r1[0][0], self.r2[0][0]
            inv_sqrt2 = 1.0 / math.sqrt(2)
            self.r1 = [((a0 + b0) * inv_sqrt2, 0)]
            self.r2 = [((a0 - b0) * inv_sqrt2, 0)]
        else:
            self.r1 = simpRyPoint(divSqrt(self.r1) + divSqrt(self.r2))
            self.r2 = simpRyPoint(divSqrt(self.r1) + applyNeg(divSqrt(self.r2)))

    def applyMult(self, r):
        newr = []
        for e in self.r2:
            newr += [(e[0], e[1] + r)]
        self.r2 = newr

    def flip(self):
        v = self.r2
        self.r2 = self.r1
        self.r1 = v
