from typing import List
from qetast.nodes import QXRoot
from qetast.program import QETASTGenerator


def get_applied_ast(ast: QXRoot, apps: List[QETASTGenerator]) -> QXRoot:
    for app in apps:
        ast = app.visitRoot(ast)

    return ast
