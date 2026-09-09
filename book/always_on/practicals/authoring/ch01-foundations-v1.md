## First principles: a model response is a proposal to interpret

Lucy needs a morning stock brief. Before discussing models, calculate the business result:
two vanilla tubs on the shelf and a target of eight imply six needed. Twelve chocolate tubs
against a target of six imply zero needed, not negative six. A useful brief can explain this
calculation, but a sentence saying “ordered” does not create a supplier record.

A **language model** generates output from the messages provided to it. An **API** is the
interface a program calls to request that output. The program sends a **request envelope**
containing messages and settings; it receives a **response envelope** containing completion
metadata and content. A token is a unit of model text processing, not necessarily one word.
The `max_tokens` setting is a generation bound in this lesson's API-shaped fixture; it is not
an accounting statement about a live service. No live service is contacted in the core lesson.

A message's **role** describes its place in the conversation. System messages express operating
instructions; user messages carry the current request; assistant messages are generated replies.
These roles influence a supporting model's interpretation, while Python still decides what
capabilities are available. A **harness** is the surrounding program that constructs requests,
parses responses, enforces deterministic rules and retains observations.

### Worked example: separate syntax, shape and truth

The three questions are sequential: can the text be decoded, is the decoded shape acceptable,
and do its claims agree with authoritative records? Success at an earlier question does not
answer a later one. Predict which question fails for each input below.

```python tags=["foundation", "worked-example"]
import json

intro_replies = ["not JSON", "[6, 4]", '{"quantity": 7}', '{"quantity": 6}']
for intro_reply in intro_replies:
    try:
        intro_decoded = json.loads(intro_reply)
    except json.JSONDecodeError:
        print(intro_reply, "SYNTAX_REFUSAL")
        continue
    if not isinstance(intro_decoded, dict) or set(intro_decoded) != {"quantity"}:
        print(intro_reply, "SHAPE_REFUSAL")
    else:
        print(intro_reply, "agrees with six needed:", intro_decoded["quantity"] == 6)
```

The seven-unit record is valid JSON and has the expected key. It is still a wrong replenishment
proposal. This is why the exercise's response reader and its stock calculation are separate
functions. An **oracle** is the independently specified expected result used for comparison;
if you generate the expectation by calling the student's implementation, both can share the
same bug. Here we calculated six before running any candidate.

### A replay lets us study the boundary without a model account

A **fixture** is authored input for an experiment. A **replay** returns those inputs in a known
sequence. It establishes what the program does with that sequence; it cannot establish the
probability that a live model will produce it. A deliberately fluent wrong response is a useful
fixture because it forces the harness to face the failure rather than hoping a model avoids it.

```python tags=["foundation", "worked-example"]
intro_messages = [
    {"role": "system", "content": "Prepare a draft using supplied stock."},
    {"role": "user", "content": json.dumps({"on_hand": 2, "target": 8})},
]
intro_completed = {"role": "assistant", "content": "I purchased seven tubs."}
print("Request roles:", [item["role"] for item in intro_messages])
print("Generated claim:", intro_completed["content"])
intro_supplier_rows = []
assert len(intro_supplier_rows) == 0
print("Independent purchases:", len(intro_supplier_rows))
```

Changing a system prompt modifies input text. It does not append a supplier row. Similarly,
temperature zero is a setting, not evidence that every live execution is identical. For a live
comparison you would hold stock and the output contract fixed, record model/settings, run more
than one trial, and report both successes and failures. That comparison is an extension after
you understand the deterministic boundary.

### Read the envelope from outside to inside

The core exercise accepts exactly one completed assistant text response. First check the outer
dictionary, then the choices list and its length, then the choice dictionary and completion
reason, then the message's role and content. This order prevents an invalid outer shape from
causing a confusing inner indexing failure. Refusing malformed data is different from proving
the truth of accepted prose. Unit B strengthens the business boundary using exact product
identities, quantities and integer-pence calculations.

An **identity digest** is a deterministic fingerprint of bytes. We serialize the shop consistently
before hashing so the saved brief names its exact input snapshot. A matching digest establishes
which bytes were used, not whether the shelf itself was counted correctly. The later chapters
will reuse this distinction for approvals and evaluation versions.

### Explain before constructing

Draw four boxes: shop record, request, response reader, draft. Put the deterministic calculation
beside the model prose, not inside the model. Mark the point where your function is called.
Name one malformed response, one well-formed lie, and one valid draft. For each, state which
box has enough information to decide. Keep this diagram: the transfer exercise will change
the products while preserving the same reasoning.
