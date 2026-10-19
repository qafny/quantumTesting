"""Instrument existing transform methods without introducing another base class."""

from functools import wraps
from time import perf_counter


def instrument_pass_classes(classes):
    for cls in classes:
        original = cls.transform
        if getattr(original, "_qet_timed", False):
            continue

        def wrap(method):
            @wraps(method)
            def timed(self, circuit):
                start = perf_counter()
                try:
                    return method(self, circuit)
                finally:
                    self.transform_time_s = perf_counter() - start
            timed._qet_timed = True
            return timed

        cls.transform = wrap(original)
