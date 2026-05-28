import math


def divSqrt(r:list[tuple[float, int]]):
    newr = []
    for e in r:
        newr += [(e[0] / math.sqrt(2),e[1])]
    return newr


def applyNeg(r:list[tuple[float, int]]):
    newr = []
    for e in r:
        newr += [(-e[0],e[1])]
    return newr


def simpRyPoint(r:list[tuple[float, int]]):
    newr = []
    for e in r:
        if e[0] != 0:
            newr += [(e[0],e[1])]
    return newr


def addto(r, n, rmax):
    return (r + 2 ** max_helper(rmax, n)) % 2 ** rmax


def max_helper(x, y):
    return max(x - y, 0)


def rotate(r, n, rmax):
    return addto(r, n, rmax)


def addto_n(r, n, rmax):
    return max_helper(r + 2 ** rmax, 2 ** max_helper(rmax, n)) % 2 ** rmax


def r_rotate(r, n, rmax):
    return addto_n(r, n, rmax)


def natminusmod(x, v, a):
    if x - v < 0:
        return x - v + a
    else:
        return x - v


def bit_array_to_int(bit_array, num_qubits):
    val = 0
    for i in range(min(len(bit_array), num_qubits)):
        val += pow(2, i) * int(bit_array[i])
    return val


def to_binary_arr(value, array_length):
    binary_arr = [False] * array_length
    for i in range(array_length):
        b = value % 2
        value = value // 2
        binary_arr[i] = bool(b)
    return binary_arr


def calBin(val, num):
    return to_binary_arr(val, num)


def calBinNoLength(v):
    val = []
    while v != 0:
        b = v % 2
        v = v // 2
        val.append(b)
    return val
