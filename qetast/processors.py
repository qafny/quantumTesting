from qetast.nodes import QXMarkedNode, QXDummyNode
from qetast.program import QETASTGenerator


class MarkedNodeEliminator(QETASTGenerator):

    def visitMarkedNode(self, node: QXMarkedNode):
        return QXDummyNode()
