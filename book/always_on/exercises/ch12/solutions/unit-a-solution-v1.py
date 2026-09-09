"""Instructor reference; execute only in the submitted Unit A namespace."""

# ruff: noqa: F821
implementation_source = r'''
def baseline(case: Case) -> list[tuple[str, int]]:
    """The simpler design against which the agent must earn its extra cost."""
    return [
        (sku, threshold - stock + reserved)
        for sku, stock, reserved, threshold, _ in case.stock
        if stock - reserved < threshold
    ]
'''
assert connect_build(implementation_source)["status"] == "PASS"
