from typing import Dict
from generators.inputs import CompleteInputSpaceGenerator, RandomInputGenerator


def get_standard_input_generator(generator_identifier: str, kwargs: Dict):
    match generator_identifier:
        case CompleteInputSpaceGenerator.get_identifier():
            return CompleteInputSpaceGenerator(**kwargs)
        case RandomInputGenerator.get_identifier():
            return RandomInputGenerator(**kwargs)
        case _:
            return None
