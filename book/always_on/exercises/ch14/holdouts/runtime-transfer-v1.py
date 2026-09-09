"""Instructor transfer cases exercise the actual copied runtime, with independent answers."""

import json
import tempfile
from pathlib import Path

from reference_organizations.store.agent import seed_lucy
from sovereign_agent.database import Database

with tempfile.TemporaryDirectory(prefix="lucy-transfer-") as directory:
    state = Path(directory)
    db = Database(state / "agent.sqlite")
    seed_lucy(db)
    from pydantic import ValidationError

    from reference_organizations.store.delegation import Inquiry, quote

    for guests, tubs in ((1, 1), (10, 1), (17, 2), (20, 2), (199, 20), (200, 20)):
        result = quote(db, Inquiry(sku="SKU-VANILLA", guests=guests))
        assert result["tubs"] == tubs and result["total_pence"] == tubs * 500
        assert result["status"] == "DRAFT_QUOTE" and result["stock_reserved"] is False
    for guests in (0, 201, True, "17"):
        try:
            Inquiry(sku="SKU-VANILLA", guests=guests)
        except ValidationError:
            pass
        else:
            raise AssertionError("invalid inquiry")
    with db.immediate() as c:
        row = json.loads(
            c.execute("SELECT record FROM products WHERE sku='SKU-VANILLA'").fetchone()[0]
        )
        row["price_cents"] = 317
        c.execute("UPDATE products SET record=? WHERE sku='SKU-VANILLA'", (json.dumps(row),))
    assert quote(db, Inquiry(sku="SKU-VANILLA", guests=21))["total_pence"] == 951
    assert db.connection.execute("SELECT count(*) FROM assistant_orders").fetchone()[0] == 0
    db.close()
print(json.dumps({"passed": True}))
