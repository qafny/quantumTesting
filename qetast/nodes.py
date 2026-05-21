import copy
import time
from typing import List
from qetast.base import AbstractASTVisitor


class QXTop:

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


class QXExp(QXTop):

    def __init__(self, name: str):
        super().__init__()
        self._name = name

    def accept(self, visitor: AbstractASTVisitor):
        pass

    def name(self):
        return self._name


class QXQubit(QXTop):

    def __init__(self, idx: str):
        super().__init__()

        self._idx = idx

    def accept(self, visitor: AbstractASTVisitor):
        return visitor.visitQubit(self)

    def ID(self):
        return self._idx


class QXConstant(QXTop):

    def __init__(self, value: float):
        super().__init__()
        self._value: float = value

    def accept(self, visitor: AbstractASTVisitor):
        return visitor.visitConstant(self)

    def value(self):
        return self._value


class QXRoot(QXTop):

    def __init__(self, program: QXProgram, qubits: List[QXQubit]):
        super().__init__()
        self._program = program
        self._qubits = qubits

    def accept(self, visitor: AbstractASTVisitor):
        return visitor.visitRoot(self)

    def program(self):
        return self._program

    def qubits(self):
        return self._qubits


class QXProgram(QXTop):

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

    def accept(self, visitor : AbstractASTVisitor):
        return visitor.visitH(self)


class QXX(QXQGate):

    def __init__(self, qubit_idx: str, name: str = None):
        super().__init__(qubit_idx, name = name)

    def accept(self, visitor: AbstractASTVisitor):
        return visitor.visitX(self)


class QXRY(QXQGate):

    def __init__(self, qubit_idx: str, phase: QXConstant, name: str = None):
        super().__init__(qubit_idx, name = name)
        self._phase = phase

    def accept(self, visitor: AbstractASTVisitor):
        return visitor.visitRY(self)

    def phase(self):
        return self._phase


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
