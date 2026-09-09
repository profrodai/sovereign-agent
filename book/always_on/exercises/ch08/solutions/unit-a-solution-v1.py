"""Instructor reference; execute only in the submitted Unit A namespace."""

# ruff: noqa: F821
implementation_source = r"""
def approve(
    db: Database,
    identifier: str,
    digest: str,
    *,
    actor: str,
    policy: SpendingPolicy,
    expires: float,
    automatic: bool = False,
    supplier: Supplier | None = None,
    now: float | None = None,
) -> None:
    now = time.time() if now is None else now
    if type(automatic) is not bool:
        raise ValueError("approval basis must be explicit")
    if not math.isfinite(expires) or not now < expires <= now + 86400:
        raise ValueError("approval must expire within one day")
    if actor not in policy.operators:
        raise PermissionError("operator is not allowlisted")
    with db.immediate() as connection:
        order = connection.execute(
            "SELECT * FROM assistant_orders WHERE id=?", (identifier,)
        ).fetchone()
        if (
            order is None
            or order["digest"] != digest
            or order["status"] not in {"DRAFT", "APPROVED", "SENDING", "UNKNOWN"}
            or order["revoked"]
        ):
            raise PermissionError("approval does not match an eligible exact proposal")
        _operator_state(db)
        work = connection.execute(
            "SELECT cancelled FROM assistant_work WHERE id=?", (order["work_id"],)
        ).fetchone()
        if work["cancelled"]:
            raise PermissionError("cancelled work cannot gain new approval")
        if order["status"] in {"SENDING", "UNKNOWN"} and (
            automatic
            or supplier is None
            or not supplier.idempotent
            or supplier.identity != order["target"]
        ):
            raise PermissionError(
                "uncertain retry needs explicit approval and matching idempotent supplier"
            )
        if automatic and order["amount"] > policy.automatic_order_pence:
            raise PermissionError("exact proposal needs operator approval")
        connection.execute(
            "INSERT OR IGNORE INTO assistant_spending(id,limit_pence) VALUES (1,?)",
            (policy.total_pence,),
        )
        budget = connection.execute("SELECT * FROM assistant_spending WHERE id=1").fetchone()
        assert budget
        addition = order["amount"] if order["status"] == "DRAFT" else 0
        # A supplied policy cannot silently raise the installed account ceiling.
        if budget["spent_pence"] + budget["reserved_pence"] + addition > min(
            budget["limit_pence"], policy.total_pence
        ):
            raise PermissionError("cumulative spending ceiling reached")
        connection.execute(
            "UPDATE assistant_spending SET reserved_pence=reserved_pence+? WHERE id=1", (addition,)
        )
        connection.execute(
            "UPDATE assistant_orders SET status=CASE WHEN status IN ('SENDING','UNKNOWN') "
            "THEN status "
            "ELSE 'APPROVED' END,approved_by=?,approved_until=?,"
            "approval_basis=? WHERE id=?",
            (actor, expires, "AUTOMATIC" if automatic else "OPERATOR", identifier),
        )
        append_event(
            db,
            "assistant.order.approved",
            {"order": identifier, "digest": digest, "actor": actor, "automatic": automatic},
        )
"""
assert connect_build(implementation_source)["status"] == "PASS"
