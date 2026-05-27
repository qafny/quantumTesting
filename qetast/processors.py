from qetast.nodes import QXProgram, QXH, QXCU
from qetast.program import QETASTGenerator


class PrecedingHadamardEliminationProcessor(QETASTGenerator):

    def __init__(self):
        self.is_program_not_root: bool = False

    def visitProgram(self, node: QXProgram):
        if not self.is_program_not_root:
            tmp = []
            i = 0
            prefixed = True
            while node.exp(i) is not None:
                if prefixed:
                    if not isinstance(node.exp(i), QXH):
                        prefixed = False
                        tmp.append(node.exp(i).accept(self))
                else:
                    tmp.append(node.exp(i).accept(self))

                i += 1

            return QXProgram(tmp).instance(node.get_id())

        return super(PrecedingHadamardEliminationProcessor, self).visitProgram(node)

    def visitCU(self, node: QXCU):
        self.is_program_not_root = True
        retval = super(PrecedingHadamardEliminationProcessor, self).visitCU(node)
        self.is_program_not_root = False

        return retval


class SucceedingHadamardEliminationProcessor(QETASTGenerator):

    def __init__(self):
        self.is_program_not_root: bool = False

    def visitProgram(self, node: QXProgram):
        if not self.is_program_not_root:
            tmp = []
            i = 0
            while node.exp(i) is not None:
                tmp.append(node.exp(i).accept(self))

                i += 1

            rtmp = []
            suffixed = True
            for exp in reversed(tmp):
                if suffixed:
                    if not isinstance(exp, QXH):
                        suffixed = False
                        rtmp.append(exp)
                else:
                    rtmp.append(exp)

            rtmp.reverse()

            return QXProgram(rtmp).instance(node.get_id())

        return super(SucceedingHadamardEliminationProcessor, self).visitProgram(node)

    def visitCU(self, node: QXCU):
        self.is_program_not_root = True
        retval = super(SucceedingHadamardEliminationProcessor, self).visitCU(node)
        self.is_program_not_root = False

        return retval
