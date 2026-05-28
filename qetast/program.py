from qetast.nodes import QXRoot, QXProgram, QXQubit, QXConstant, QXH, QXX, QXRZ, QXCU, QXMarkedNode
from qetast.base import AbstractASTVisitor
from qetast.nodes import QXQubit, QXConstant, QXQGate


class QETASTVisitor(AbstractASTVisitor):

    def visit(self, node):
        if isinstance(node, QXRoot):
            return self.visitRoot(node)
        elif isinstance(node, QXProgram):
            return self.visitProgram(node)
        elif isinstance(node, QXQubit):
            return self.visitQubit(node)
        elif isinstance(node, QXConstant):
            return self.visitConstant(node)
        elif isinstance(node, QXQGate):
            return self.visitQGate(node)
        elif isinstance(node, QXH):
            return self.visitH(node)
        elif isinstance(node, QXX):
            return self.visitX(node)
        elif isinstance(node, QXRZ):
            return self.visitRZ(node)
        elif isinstance(node, QXCU):
            return self.visitCU(node)
        elif isinstance(node, QXMarkedNode):
            return self.visitMarkedNode(node)
        else:
            raise Exception(f"Unknown node: {node}")

    def visitRoot(self, node: QXRoot):
        return node.program().accept(self)

    def visitProgram(self, node: QXProgram):
        retval = True
        i = 0
        while node.exp(i) is not None:
            retval = node.exp(i).accept(self) and retval
            i += 1

        return retval

    def visitQubit(self, node: QXQubit):
        return True

    def visitQGate(self, node: QXQGate):
        return True

    def visitConstant(self, node: QXConstant):
        return True

    def visitH(self, node: QXH):
        return True

    def visitX(self, node: QXX):
        return True

    def visitRZ(self, node: QXRZ):
        return node.phase().accept(self)

    def visitCU(self, node: QXCU):
        return node.program().accept(self)

    def visitMarkedNode(self, node: QXMarkedNode):
        return node.elem().accept(self)


class QETASTGenerator(QETASTVisitor):

    def visitRoot(self, node: QXRoot):
        program = node.program().accept(self)
        qubits = [qubit.accept(self) for qubit in node.qubits()]
        return QXRoot(program, qubits).instance(node.get_id())

    def visitProgram(self, node: QXProgram):
        i = 0
        tmp = []
        while node.exp(i) is not None:
            tmp.append(node.exp(i).accept(self))
            i += 1

        return QXProgram(tmp).instance(node.get_id())

    def visitQubit(self, node: QXQubit):
        return QXQubit(node.ID()).instance(node.get_id())

    def visitConstant(self, node: QXConstant):
        return QXConstant(node.value()).instance(node.get_id())

    def visitQGate(self, node: QXQGate):
        return QXQGate(node.qubit(), node.name()).instance(node.get_id())

    def visitH(self, node: QXH):
        return QXH(node.qubit(), node.name()).instance(node.get_id())

    def visitX(self, node: QXX):
        return QXX(node.qubit(), node.name()).instance(node.get_id())

    def visitRZ(self, node: QXRZ):
        phase = node.phase().accept(self)
        return QXRZ(node.qubit(), phase, node.name()).instance(node.get_id())

    def visitCU(self, node: QXCU):
        program = node.program().accept(self)
        return QXCU(node.qubit(), program, node.name()).instance(node.get_id())

    def visitMarkedNode(self, node: QXMarkedNode):
        return QXMarkedNode(node.elem().accept()).instance(node.get_id())
