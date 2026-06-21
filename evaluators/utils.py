import numpy as np


def zcomplex(c: complex) -> complex:
    return complex(np.round(c.real, decimals=8), np.round(c.imag, decimals=8))
