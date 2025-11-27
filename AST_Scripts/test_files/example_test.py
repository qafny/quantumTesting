import sys
import os

current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)
sys.path.insert(0,parent_dir)
sys.path.insert(0,grandparent_dir)

from XMLProgrammer import * 
from AbstractProgramVisitor import *

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
