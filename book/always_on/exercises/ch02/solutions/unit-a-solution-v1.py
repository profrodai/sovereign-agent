"""Instructor reference; execute only in the submitted Unit A namespace."""

# ruff: noqa: F821
implementation_source = r"""
def build_tools(shop):
    rows = {row["sku"]: copy.deepcopy(row) for row in shop["products"]}
    if len(rows) != len(shop["products"]):
        raise ValueError("duplicate product identity")

    def stock(_):
        return [
            {**row, "needed": max(0, row["reorder_point"] - row["on_hand"])}
            for _, row in sorted(rows.items())
        ]

    def quote(args):
        if args.sku not in rows:
            raise KeyError("unknown product")
        return {
            "sku": args.sku,
            "supplier": "lucy-local",
            "currency": "GBP",
            "unit_cost_pence": PRICES[args.sku],
        }

    def draft(args):
        row = rows[args.sku]
        needed = max(0, row["reorder_point"] - row["on_hand"])
        if args.quantity != needed:
            raise ValueError("quantity differs from the replenishment need")
        price = quote(ProductArguments(sku=args.sku))
        return {
            **price,
            "quantity": args.quantity,
            "total_pence": args.quantity * price["unit_cost_pence"],
            "status": "DRAFT",
        }

    registered = [
        ExecutableTool("list_stock", "Read stock and calculated need.", NoArguments, stock),
        ExecutableTool("supplier", "Read supplier price in GBP pence.", ProductArguments, quote),
        ExecutableTool("draft_order", "Calculate a draft; never purchases.", DraftArguments, draft),
    ]
    return Dispatcher(registered, allowed=frozenset(tool.name for tool in registered))
"""
assert connect_build(implementation_source)["status"] == "PASS"
