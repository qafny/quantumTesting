def parse_gate_list(value: str) -> list[str]:
    return [
        gate.strip().lower()
        for gate in value.split(",")
        if gate.strip()
    ]


def parse_int_list(value: str) -> list[int]:
    return [
        int(item.strip())
        for item in value.split(",")
        if item.strip()
    ]