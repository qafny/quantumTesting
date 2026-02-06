def greaterThan(n: int):
    return n > 3

properties = dict(
    AndGate = greaterThan
)

#below line is just for proof of concept
print(properties["AndGate"](2))

from hypothesis import given, strategies as st, assume, settings, HealthCheck
@given(st.integers())
def test_bad_property(x):
    assert greaterThan(x)