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
    from sovereign_agent.telegram_channel import poll

    class Bot:
        account = "transfer"

        def __init__(self, updates):
            self.updates = updates

        def call(self, method, data):
            return self.updates

    def update(i, kind="private", actor=817, chat=817):
        return {
            "update_id": i,
            "message": {
                "from": {"id": actor, "is_bot": False},
                "chat": {"id": chat, "type": kind},
                "text": "Brief me",
            },
        }

    bot = Bot(
        [
            update(84),
            update(80),
            update(83, "supergroup"),
            update(82, actor=999),
            update(81, chat=900),
        ]
    )
    assert len(poll(db, bot, frozenset({817}))) == 2
    assert db.connection.execute("SELECT offset FROM assistant_channel_cursor").fetchone()[0] == 85
    db.close()
    db = Database(state / "agent.sqlite")
    assert poll(db, bot, frozenset({817})) == []
    assert db.connection.execute("SELECT count(*) FROM assistant_work").fetchone()[0] == 2
    bot.updates = [update(86), {"update_id": True}]
    try:
        poll(db, bot, frozenset({817}))
    except ValueError:
        pass
    else:
        raise AssertionError("invalid identity admitted")
    assert db.connection.execute("SELECT offset FROM assistant_channel_cursor").fetchone()[0] == 85
    assert db.connection.execute("SELECT count(*) FROM assistant_work").fetchone()[0] == 2
    db.close()
print(json.dumps({"passed": True}))
