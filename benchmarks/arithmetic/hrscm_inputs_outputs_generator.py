import json
from generators.inputs import RandomInputGenerator


generator = RandomInputGenerator(6, 20)
inputs = generator.generate()


def btoi(b: bool):
    return "1" if b else "0"


def itob(i: int):
    return f"{i:06b}"


expected_outputs = []
for ins in inputs:
    a = int(f"{btoi(ins["2"])}{btoi(ins["1"])}{btoi(ins["0"])}", 2)
    b = int(f"{btoi(ins["5"])}{btoi(ins["4"])}{btoi(ins["3"])}", 2)

    e = a * b % (2 ^ 6)
    eb = itob(e)

    expected = {
        "0": ins["0"],
        "1": ins["1"],
        "2": ins["2"],
        "3": ins["3"],
        "4": ins["4"],
        "5": ins["5"],
        "12": False,
    }

    for idx, iv in enumerate(reversed(eb)):
        expected[str(idx + 6)] = iv == "1"

    expected_outputs.append(expected)


for idx in range(len(inputs)):
    for i in range(6, 12):
        inputs[idx][str(i)] = False


with open("hrscm_paired_io_inputs.json", "w") as f:
    json.dump(inputs, f)


with open("hrscm_paired_io_outputs.json", "w") as f:
    json.dump(expected_outputs, f)
