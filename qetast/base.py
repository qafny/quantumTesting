from abc import ABC, abstractmethod


class AbstractASTVisitor(ABC):

    @abstractmethod
    def visit(self, node):
        pass

    @abstractmethod
    def visitRoot(self, node):
        pass

    @abstractmethod
    def visitProgram(self, ctx):
        pass

    @abstractmethod
    def visitQubit(self, ctx):
        pass

    @abstractmethod
    def visitConstant(self, ctx):
        pass

    @abstractmethod
    def visitQGate(self, ctx):
        pass

    @abstractmethod
    def visitH(self, ctx):
        pass

    @abstractmethod
    def visitX(self, ctx):
        pass

    @abstractmethod
    def visitRZ(self, ctx):
        pass

    @abstractmethod
    def visitCU(self, ctx):
        pass
