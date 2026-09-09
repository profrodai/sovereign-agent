## Memory means selecting retained evidence for a new request

Lucy says deliveries should arrive at nine, then corrects herself to ten. A useful assistant
must retain the correction after a restart and avoid presenting both times as current guidance.
**Persistence** means the record survives the process. **Retrieval** means choosing which retained
records to include now. They are separate mechanisms: a database can preserve every revision
while retrieval returns only the currently active revision for this session.

A **session** identifies the conversation or work context that owns a memory. **Provenance**
records where a value came from. A **revision** is a new version of an earlier value. Here a
correction creates current guidance while old evidence can remain available for audit. Forgetting
excludes a value from future context; it does not erase already sent provider requests or backups.

### Derive a retrieval rule on visible rows

Our small table has two sessions and two revisions. First filter by session and active status.
Then rank the remaining rows for this query. Reversing those operations can waste a limited
context budget on a foreign or superseded row. Predict the returned identities for Lucy.

```python tags=["foundation", "worked-example"]
intro_memories = [
    {"id": 1, "session": "lucy", "active": False, "name": "delivery", "value": "09:00"},
    {"id": 2, "session": "lucy", "active": True, "name": "delivery", "value": "10:00"},
    {"id": 3, "session": "another-shop", "active": True, "name": "delivery", "value": "06:00"},
    {"id": 4, "session": "lucy", "active": True, "name": "invoice", "value": "email"},
]
intro_eligible = [row for row in intro_memories if row["session"] == "lucy" and row["active"]]
print([(row["id"], row["value"]) for row in intro_eligible])
assert [row["id"] for row in intro_eligible] == [2, 4]
```

The database exercise performs the same filtering with a parameterized `WHERE` clause. The
bounded result must retain identity, name, value, source and creation evidence. Returning only
a friendly sentence would discard the provenance needed to investigate a bad answer.

### Understand the deliberately simple relevance score

We lowercase using `casefold`, split into whitespace-separated words, and count the intersection
with query words. A set intersection keeps words present in both sets. This lexical score is
easy to inspect; it is not a semantic embedding or a claim that similar meanings always match.
An **embedding** would represent text numerically for another similarity method; we do not need
that additional model or library for this lesson's explicit rule.

```python tags=["foundation", "worked-example"]
intro_query_words = set("DELIVERY time".casefold().split())
intro_ranked = []
for intro_row in intro_eligible:
    intro_words = set((intro_row["name"] + " " + intro_row["value"]).casefold().split())
    intro_ranked.append((len(intro_query_words & intro_words), intro_row["id"], intro_row["value"]))
intro_ranked.sort(key=lambda item: (-item[0], -item[1]))
print(intro_ranked)
assert intro_ranked[0] == (1, 2, "10:00")
```

The negative signs turn ascending Python sorting into descending score and descending identity.
Identity breaks ties deterministically in favor of the newer row. Slicing `[:maximum]` then
limits the output. Validate the maximum first; accepting negative slicing would quietly turn
an invalid requested budget into a different selection rule.

### Follow the context all the way to the model seam

The course's `Database` supplies durable rows. `preferences` retrieves them. The context builder
places selected values in the next request. The replay model records the actual messages it
received. A successful insert proves only persistence; a successful query proves retrieval;
the recorded message proves that the retrieved data was connected to the model input.

In Unit A you implement retrieval, close and reopen the database, then inspect the context.
In Unit B a query loses its `active=1` condition. The old value can reappear even if the new value
ranks first. The repair must exclude stale guidance rather than merely move it lower in the list.

**Before the main task:** explain which records survive an empty query, why another session's
matching word cannot grant eligibility, and what happens when two rows have the same score.
For transfer, correct twice, forget one preference, and vary the retrieval limit. Keep actual
row identities beside the final context text so a plausible-looking answer cannot conceal the
wrong revision. Authoritative current stock still comes from the shop tool, not remembered prose.
