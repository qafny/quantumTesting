from qetast.nodes import QXH, QXMarkedNode, QXProgram, QXCU, QXMeasure
from qetast.program import QETASTGenerator


class AllHadamardGatesMarker(QETASTGenerator):

    def visitH(self, node: QXH):
        return QXMarkedNode(node)


class PrefixedHadamardGatesMarker(QETASTGenerator):

    def __init__(self):
        self.prefixed: bool = True

    def visitProgram(self, node: QXProgram):
        tmp = []
        i = 0
        while node.exp(i) is not None:
            if not isinstance(node.exp(i), QXH):
                self.prefixed = False

            tmp.append(node.exp(i).accept(self))

            i += 1

        return QXProgram(tmp).instance(node.get_id())

    def visitH(self, node: QXH):
        if self.prefixed:
            return QXMarkedNode(node)
        else:
            return super(PrefixedHadamardGatesMarker, self).visitH(node)


class SuffixedHadamardGatesMarker(QETASTGenerator):

    def __init__(self):
        self.suffixed = True

    def visitProgram(self, node: QXProgram):
        tmp = []
        i = 0
        while node.exp(i) is not None:
            tmp.append(node.exp(i))

            i += 1

        rtmp = []
        for exp in reversed(tmp):
            if not isinstance(exp, QXH):
                self.suffixed = False

            rtmp.append(exp.accept(self))

        rtmp.reverse()

        return QXProgram(rtmp).instance(node.get_id())

    def visitH(self, node: QXH):
        if self.suffixed:
            return QXMarkedNode(node)
        else:
            return super(SuffixedHadamardGatesMarker, self).visitH(node)


class MeasureGateMarker(QETASTGenerator):

    def visitMeasure(self, node: QXMeasure):
        return QXMarkedNode(node)