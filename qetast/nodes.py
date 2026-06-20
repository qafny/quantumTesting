import copy
import time
from typing import List
from qetast.base import AbstractASTVisitor


class QXNode:

    def __init__(self):
        self.uid = str(id(self)) + str(time.time())

    def set_id(self, uid: str):
        self.uid = uid

    def get_id(self) -> str:
        return self.uid

    def instance(self, uid: str):
        self.set_id(uid)
        return self

    def accept(self, visitor):
        pass

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result

        for k, v in self.__dict__.items():
            setattr(result, k, copy.deepcopy(v, memo))

        return result


class QXExp(QXNode):

    def __init__(self, name: str):
        super().__init__()
        self._name = name

    def accept(self, visitor: AbstractASTVisitor):
        pass

    def name(self):
        return self._name


class QXQubit(QXNode):

    def __init__(self, idx: str):
        super().__init__()

        self._idx = idx

    def accept(self, visitor: AbstractASTVisitor):
        return visitor.visitQubit(self)

    def ID(self):
        return self._idx


class QXConstant(QXNode):

    def __init__(self, value: float):
        super().__init__()
        self._value: float = value

    def accept(self, visitor: AbstractASTVisitor):
        return visitor.visitConstant(self)

    def value(self):
        return self._value


class QXRoot(QXNode):

    def __init__(self, program: QXProgram, qubits: List[QXQubit], global_phase: float = 0.0):
        super().__init__()
        self._program = program
        self._qubits = qubits
        self._global_phase = global_phase

    def accept(self, visitor: AbstractASTVisitor):
        return visitor.visitRoot(self)

    def program(self):
        return self._program

    def qubits(self):
        return self._qubits

    def global_phase(self):
        return self._global_phase


class QXProgram(QXNode):

    def __init__(self, exps: List[QXExp]):
        super().__init__()
        self._exps = exps

    def accept(self, visitor: AbstractASTVisitor):
        return visitor.visitProgram(self)

    def exp(self, i: int = None):
        return self._exps[i] if len(self._exps) > i else None


class QXQGate(QXExp):

    def __init__(self, qubit_idx: str, name: str = None):
        super().__init__(name)
        self._qubit = qubit_idx

    def accept(self, visitor: AbstractASTVisitor):
        return visitor.visitQGate(self)

    def qubit(self):
        return self._qubit


class QXH(QXQGate):

    def __init__(self, qubit_idx: str, name: str = None):
        super().__init__(qubit_idx, name = name)

    def accept(self, visitor: AbstractASTVisitor):
        return visitor.visitH(self)


class QXX(QXQGate):

    def __init__(self, qubit_idx: str, name: str = None):
        super().__init__(qubit_idx, name = name)

    def accept(self, visitor: AbstractASTVisitor):
        return visitor.visitX(self)


class QXRZ(QXQGate):

    def __init__(self, qubit_idx: str, phase: QXConstant, name: str = None):
        super().__init__(qubit_idx, name = name)
        self._phase = phase

    def accept(self, visitor: AbstractASTVisitor):
        return visitor.visitRZ(self)

    def phase(self):
        return self._phase


class QXCU(QXQGate):

    def __init__(self, qubit_idx: str, program: QXProgram, name: str = None):
        super().__init__(qubit_idx, name = name)
        self._program = program

    def accept(self, visitor: AbstractASTVisitor):
        return visitor.visitCU(self)

    def program(self):
        return self._program


class QXMeasure(QXQGate):
    
    def __init__(self, qubit_idx: str, name: str = None):
        super().__init__(qubit_idx, name)

    def accept(self, visitor: AbstractASTVisitor):
        return visitor.visitMeasure(self)


class QXMarkedNode(QXNode):

    def __init__(self, elem: QXNode):
        super().__init__()
        self._elem = elem

    def accept(self, visitor: AbstractASTVisitor):
        return visitor.visitMarkedNode(self)

    def elem(self):
        return self._elem


class QXDummyNode(QXNode):

    def __init__(self):
        super().__init__()

    def accept(self, visitor: AbstractASTVisitor):
        return visitor.visitDummyNode(self)
