"""Instructor reference; execute only in the submitted Unit A namespace."""

# ruff: noqa: F821
implementation_source = r'''
def quote(db: Database, inquiry: Inquiry) -> dict[str, Any]:
    """Ten portions per tub is Lucy's authored catering fixture, not a model estimate."""
    row = db.connection.execute(
        "SELECT record FROM products WHERE sku=?", (inquiry.sku,)
    ).fetchone()
    if row is None:
        raise ValueError("unknown catering product")
    price = json.loads(row[0])["price_cents"]
    if type(price) is not int or price <= 0:
        raise ValueError("invalid catalog selling price")
    tubs = (inquiry.guests + 9) // 10
    return {
        "sku": inquiry.sku,
        "guests": inquiry.guests,
        "portions_per_tub": 10,
        "tubs": tubs,
        "total_pence": tubs * price,
        "currency": "GBP",
        "status": "DRAFT_QUOTE",
        "stock_reserved": False,
    }
'''
assert connect_build(implementation_source)["status"] == "PASS"
