from abc import ABC, abstractmethod


class AbstractASTVisitor(ABC):

    @abstractmethod
    def visit(self, node):
        pass

    @abstractmethod
    def visitRoot(self, node):
        pass

    @abstractmethod
    def visitProgram(self, node):
        pass

    @abstractmethod
    def visitQubit(self, node):
        pass

    @abstractmethod
    def visitConstant(self, node):
        pass

    @abstractmethod
    def visitQGate(self, node):
        pass

    @abstractmethod
    def visitH(self, node):
        pass

    @abstractmethod
    def visitX(self, node):
        pass

    @abstractmethod
    def visitRZ(self, node):
        pass

    @abstractmethod
    def visitCU(self, node):
        pass

    @abstractmethod
    def visitMarkedNode(self, node):
        pass
