from qetast.nodes import QXProgram, QXH, QXCU, QXMarkedNode, QXDummyNode
from qetast.program import QETASTGenerator


class MarkedNodeEliminator(QETASTGenerator):

    def visitMarkedNode(self, node: QXMarkedNode):
        return QXDummyNode()
