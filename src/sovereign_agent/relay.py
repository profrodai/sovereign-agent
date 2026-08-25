"""Durable addressed mailbox with claim leases."""

from __future__ import annotations

from datetime import timedelta

from sovereign_agent.database import Database
from sovereign_agent.errors import Refusal
from sovereign_agent.events import append_event
from sovereign_agent.ids import new_id, utc_now
from sovereign_agent.models import Message, MessageState

LEASE = timedelta(minutes=15)
MAX_RETRIES = 3


def send(db: Database, sender: str, recipient: str, subject: str, body: str) -> Message:
    message = Message(
        id=new_id("msg"),
        sender=sender,
        recipient=recipient,
        subject=subject,
        body=body,
        state=MessageState.NEW,
        created_at=utc_now(),
    )
    with db.transaction():
        db.put("messages", message.id, message.model_dump(mode="json"))
        append_event(db, "message.sent", {"id": message.id, "recipient": recipient})
    return message


def inbox(db: Database, actor_id: str) -> list[Message]:
    rows = db.connection.execute(
        "SELECT record FROM messages WHERE recipient = ?", (actor_id,)
    ).fetchall()
    messages = [Message.model_validate_json(row["record"]) for row in rows]
    now = utc_now()
    visible: list[Message] = []
    for message in messages:
        if (
            message.state == MessageState.CLAIMED
            and message.claim_expires_at is not None
            and message.claim_expires_at <= now
        ):
            message.state = MessageState.NEW
            message.claim_owner = None
            db.put("messages", message.id, message.model_dump(mode="json"))
        if message.state in {MessageState.NEW, MessageState.CLAIMED}:
            visible.append(message)
    return visible


def claim(db: Database, message_id: str, actor_id: str) -> Message:
    raw = db.get("messages", "id", message_id)
    if raw is None:
        raise Refusal(
            "Message missing.",
            "Addresses are exact actor ids.",
            "sovereign-agent inbox",
            "Use a real actor id.",
        )
    message = Message.model_validate(raw)
    if message.recipient != actor_id:
        raise Refusal(
            happened=f"{actor_id} cannot claim a message addressed to {message.recipient}.",
            why="A newly invented subagent is not an independently governed actor.",
            inspect="sovereign-agent actor list",
            next_command="Claim only with the addressed actor id.",
        )
    if message.state == MessageState.CLAIMED and message.claim_owner == actor_id:
        return message
    if message.state != MessageState.NEW:
        raise Refusal(
            "Message is not claimable.",
            "Claims are exclusive.",
            "sovereign-agent inbox",
            "Wait for lease expiry.",
        )
    message.state = MessageState.CLAIMED
    message.claim_owner = actor_id
    message.claim_expires_at = utc_now() + LEASE
    with db.transaction():
        db.put("messages", message.id, message.model_dump(mode="json"))
        append_event(db, "message.claimed", {"id": message.id, "actor_id": actor_id})
    return message


def complete(db: Database, message_id: str, actor_id: str) -> Message:
    message = Message.model_validate(db.get("messages", "id", message_id) or {})
    if message.claim_owner != actor_id:
        raise Refusal(
            "Only the claimant can complete a message.",
            "Mailbox claims are exclusive.",
            "inbox",
            "claim first",
        )
    message.state = MessageState.DONE
    with db.transaction():
        db.put("messages", message.id, message.model_dump(mode="json"))
        append_event(db, "message.done", {"id": message.id})
    return message


def dead_letter(db: Database, message: Message) -> Message:
    if message.retry_count < MAX_RETRIES:
        message.retry_count += 1
        message.state = MessageState.NEW
        message.claim_owner = None
    else:
        message.state = MessageState.DEAD
    db.put("messages", message.id, message.model_dump(mode="json"))
    return message
