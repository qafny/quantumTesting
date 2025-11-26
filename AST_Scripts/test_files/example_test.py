import sys
sys.path.append('/Users/anshugsharma/VSCodeRepos/quantumTesting')
from AST_Scripts.XMLProgrammer import *
from AST_Scripts.AbstractProgramVisitor import *

# example from https://docs.pytest.org/en/stable/
def inc(x):
    return x + 1

def test_answer():
    assert inc(3) == 4

def test_qxexp():
    test = QXProgram([QXExp()])
    assert type(test.exp(0)) == QXExp

def test_not_qxexp():
    test = QXProgram([])
    assert not type(test.exp(0)) == QXExp

def test_qxroot_prog():
    test = QXRoot(QXProgram([QXExp()]))
    assert type(test.program()) == QXProgram
