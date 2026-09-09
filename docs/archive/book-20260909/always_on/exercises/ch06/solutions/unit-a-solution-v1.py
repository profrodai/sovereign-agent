"""Instructor reference; execute only in the submitted Unit A namespace."""

# ruff: noqa: F821
implementation_source = r"""
def _poll_owned(
    db: Database, bot: Bot, operators: frozenset[int], channel: str, owner: str
) -> list[str]:
    cursor = db.connection.execute(
        "SELECT offset FROM assistant_channel_cursor WHERE channel=?", (channel,)
    ).fetchone()
    offset = cursor[0] if cursor else 0
    updates = bot.call(
        "getUpdates",
        {"offset": offset, "limit": 100, "timeout": 20, "allowed_updates": ["message"]},
    )
    if not isinstance(updates, list) or len(updates) > 100:
        raise ValueError("invalid Telegram update batch")
    identifiers = []
    with db.immediate() as connection:
        current = connection.execute(
            "SELECT 1 FROM assistant_channel_leases WHERE channel=? AND owner=? AND expires>?",
            (channel, owner, time.time()),
        ).fetchone()
        if not current:
            raise PermissionError("poller claim expired")
        highest = offset - 1
        for update in updates:
            if not isinstance(update, dict):
                raise ValueError("invalid Telegram update object")
            update_id = update.get("update_id")
            if type(update_id) is not int or update_id < 0:
                raise ValueError("invalid update identity")
            # Do not discard an earlier member of an unordered batch. The cursor
            # is published only after every accepted payload is durable.
            highest = max(highest, update_id)
            message = update.get("message", {})
            if not isinstance(message, dict):
                raise ValueError("invalid Telegram message object")
            sender = message.get("from", {})
            chat = message.get("chat", {})
            if not isinstance(sender, dict) or not isinstance(chat, dict):
                raise ValueError("invalid Telegram sender or chat object")
            actor = sender.get("id")
            text = message.get("text")
            if (
                type(actor) is int
                and actor in operators
                and chat.get("type") == "private"
                and type(chat.get("id")) is int
                and chat.get("id") == actor
                and not sender.get("is_bot")
                and isinstance(text, str)
                and text.strip()
                and len(text.encode()) <= 16_384
            ):
                origin = f"{channel}:{update_id}"
                existed = connection.execute(
                    "SELECT id FROM assistant_work WHERE origin=?", (origin,)
                ).fetchone()
                identifier = _enqueue(
                    connection, origin, f"{channel}:{actor}", text, time.time(), channel, str(actor)
                )
                if not existed:
                    identifiers.append(identifier)
        connection.execute(
            "INSERT INTO assistant_channel_cursor(channel,offset) VALUES (?,?) "
            "ON CONFLICT(channel) DO UPDATE SET offset=excluded.offset",
            (channel, max(offset, highest + 1)),
        )
    return identifiers
"""
assert connect_build(implementation_source)["status"] == "PASS"
