"""Instructor reference; execute only in the submitted Unit A namespace."""

# ruff: noqa: F821
implementation_source = r"""
def preferences(
    db: Database, session: str, query: str = "", *, maximum: int = 20
) -> list[dict[str, Any]]:
    if not 1 <= maximum <= 100:
        raise ValueError("bounded retrieval required")
    words = set(query.casefold().split())
    rows = [
        dict(row)
        for row in db.connection.execute(
            "SELECT id,name,value,source,created FROM assistant_preferences "
            "WHERE session=? AND active=1",
            (session,),
        )
    ]
    for row in rows:
        row["score"] = len(words & set((row["name"] + " " + row["value"]).casefold().split()))
    return sorted(rows, key=lambda row: (-row["score"], -row["id"]))[:maximum]
"""
assert connect_build(implementation_source)["status"] == "PASS"
