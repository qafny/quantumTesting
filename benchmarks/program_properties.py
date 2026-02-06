def greaterThan(n: int):
    return n > 3

properties = dict(
    AndGate = greaterThan
)

#below line is just for proof of concept
print(properties["AndGate"](2))