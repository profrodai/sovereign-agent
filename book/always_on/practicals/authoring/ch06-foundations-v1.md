## Messaging is durable intake followed by separately observed delivery

Lucy sends a message from her phone. The assistant must decide whether it belongs to an authorized
private conversation, record it once, and arrange work. A **transport** moves messages between
systems. An **adapter** translates that transport's data into the application's internal shape.
The offline fixture implements this adapter boundary without a Telegram account or network call.
It proves local intake behavior; a live phone session requires separate transport evidence.

An incoming **update** has a transport identifier. A **cursor** records how far the poller has
durably processed updates. A **poll** asks for a batch after that cursor. A batch may be repeated
after a reconnect, so receipt is not permission to enqueue the same work again. **Deduplication**
recognizes a stable origin identity and avoids creating a second local work item for it.

### A sender and a conversation are different identities

An allowlisted person can write in a group. Checking only the sender's identity would route that
group message into a supposedly private session. The contract therefore checks chat kind and
matching sender/chat identity as well as the allowlist. A boolean is not an acceptable account
identifier even though Python considers `bool` a subclass of `int`.

```python tags=["foundation", "worked-example"]
intro_updates = [
    {"id": 12, "sender": 7, "chat": 7, "kind": "private", "text": "Opening check"},
    {"id": 13, "sender": 7, "chat": -50, "kind": "group", "text": "Opening check"},
    {"id": 14, "sender": True, "chat": True, "kind": "private", "text": "Opening check"},
]
for intro_update in intro_updates:
    intro_private = (
        type(intro_update["sender"]) is int
        and type(intro_update["chat"]) is int
        and intro_update["sender"] == intro_update["chat"]
        and intro_update["sender"] in {7}
        and intro_update["kind"] == "private"
    )
    print(intro_update["id"], intro_private)
```

The first message is admitted; the other two are refused. Changing the text to sound familiar
must not change those identity decisions. Text is content, not proof of the actor's identity.
The core task adds batch bounds, lease ownership, exact types and persistent enqueueing.

### Advance the cursor only with durable work

Imagine recording cursor 14 and crashing before storing update 14's work. The next poll starts
after 14 and loses that request. Reversing the operations without a transaction can instead
duplicate work after a crash. The local intake rows and cursor advance belong in one transaction,
with unique origin identities protecting replay. This is a local atomicity claim, not a claim
that a transport and SQLite participate in one distributed transaction.

```python tags=["foundation", "worked-example"]
intro_seen = set()
intro_work = []
intro_cursor = 0
for intro_batch in ([14, 12, 13], [12, 13, 14], [15]):
    for intro_update_id in sorted(intro_batch):
        intro_origin = ("fixture-account", intro_update_id)
        if intro_origin not in intro_seen:
            intro_seen.add(intro_origin)
            intro_work.append(intro_origin)
    intro_cursor = max([intro_cursor, *intro_batch])
    print("cursor", intro_cursor, "work count", len(intro_work))
assert len(intro_work) == 4
```

This small set model explains the identity rule; it does not survive a restart. The real exercise
uses SQLite, closes and reopens its connection, and inspects retained work and cursor evidence.
Including the account in the identity prevents two accounts' update 12 from being mistaken for
one event. Sorting gives a predictable order; do not assume transport arrival order is sorted.

### A reply can be accepted while its acknowledgement is lost

Outbound delivery has another ambiguity. If the transport accepted a reply but the caller lost
the acknowledgement, a local timeout does not prove the reply was never delivered. **UNKNOWN**
means evidence is insufficient to choose success or failure. Automatically sending another
message can create a duplicate. The notebook records intake and delivery state separately so
an accepted incoming request is not mislabeled as proof of a delivered outgoing response.

The course `_poll_owned` function runs while holding a valid poll lease. A **lease** is a time-
bounded ownership claim; the transaction checks that claim before modifying durable state.
`_enqueue` is a supplied helper that creates the internal work item. Your implementation decides
which validated updates reach it and when the cursor advances. In Unit B the broken predicate
admits group messages; observing the actual work count exposes the effect.

Before the main exercise, write predictions for an empty batch, a reordered batch, a duplicate,
a second account and an overlong text. State whether each should create work, move the cursor,
both or neither under the stated contract. For a rejected malformed batch, test that neither
earlier rows nor the cursor were partially changed.
