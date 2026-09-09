## A skill is versioned guidance with declared requirements

Lucy wants the same opening check every morning: inspect stock, review deliveries and prepare
drafts for shortages. A **skill** packages a reusable procedure with a name, version and declared
tool requirements. Its text guides a model; it does not create a new Python capability or grant
permission to call a registered tool. Keep “what the procedure requests” separate from “what
this worker is allowed to execute.”

The book stores readable skill definitions in **TOML**, a configuration format with named keys,
strings, arrays and tables. Python's `tomllib` reads TOML into ordinary Python objects. The `loads`
method reads a string; `load` reads a binary file. Parsing checks syntax, while your application
still checks required fields and meaning. You do not need a separate TOML package on Python 3.14.

### Read one procedure as data

Predict the Python type of `requires`, then compare the required capabilities with the worker's
allowlist. A subset test means *all* requirements must be available; a nonempty intersection
would prove only that at least one requirement is available.

```python tags=["foundation", "worked-example"]
import tomllib

intro_skill = tomllib.loads("""
name = "opening-review"
version = 2
requires = ["list_stock", "supplier"]
instructions = "Inspect stock and compare the supplier quote before drafting."
""")
intro_required = set(intro_skill["requires"])
for intro_allowed in ({"list_stock"}, {"list_stock", "supplier"}, set()):
    print(sorted(intro_allowed), "eligible:", intro_required <= intro_allowed)
assert not intro_required <= {"list_stock"}
assert intro_required <= {"list_stock", "supplier"}
```

A **staged** version is available for inspection and evaluation. An **active** version is the
one admitted into current context. Staging alone should not change behavior. Keeping versions
immutable lets an evaluation name the exact procedure it tested. If a file's contents change
under the same version identity, the evidence no longer has a stable subject.

### Build context within an explicit byte budget

Context is the input assembled for the next model request: selected skills, current preferences,
relevant history and the new user request. More context is not automatically better. A limit
forces an explicit admission policy and prevents an unbounded history from consuming the budget.
This implementation measures UTF-8 encoded JSON bytes, which differ from characters and model
tokens. Predict why the non-ASCII example below has a larger encoded length.

```python tags=["foundation", "worked-example"]
import json

for intro_text in ("cafe", "café", "🍦"):
    intro_bytes = intro_text.encode("utf-8")
    print(repr(intro_text), "characters:", len(intro_text), "UTF-8 bytes:", len(intro_bytes))
intro_items = [{"kind": "skill", "text": "Inspect stock."}, {"kind": "memory", "text": "10:00"}]
intro_context = []
intro_limit = 60
for intro_item in intro_items:
    intro_candidate = [*intro_context, intro_item]
    if len(json.dumps(intro_candidate, ensure_ascii=False).encode("utf-8")) <= intro_limit:
        intro_context = intro_candidate
print("Admitted context:", intro_context)
assert len(json.dumps(intro_context, ensure_ascii=False).encode("utf-8")) <= intro_limit
```

Notice that the example measures the complete candidate representation, including JSON brackets,
keys and separators. Adding the lengths of text values alone would undercount it. The actual
exercise preserves provenance and the declared ordering while admitting only bounded items.
It does not silently truncate an instruction halfway through a sentence and call that the same
procedure.

### History has a configuration boundary

A completed old conversation may have used another preference or skill revision. Replaying it
as current guidance can reintroduce an obsolete decision. The context builder therefore needs
to select revision-matching completed history. “Completed” concerns that prior episode's state;
it is not proof that every sentence it produced was factually correct.

In the core exercise, the `context` function assembles active eligible skills, explicit preferences
and bounded history. Its caller is the model-request path. Unit B removes the requirement check
and demonstrates that an active skill requiring an unavailable tool enters context. The repair
belongs in eligibility. Strengthening the skill's prose cannot replace the missing set condition.

**Explain before constructing:** what differs between a malformed TOML file, a staged but inactive
skill, an active ineligible skill and an active eligible skill that does not fit the byte budget?
Give one observation for each. Then write a new procedure with no tool requirements and explain
why an empty required set is eligible even for an empty allowlist. Eligibility still grants no
new capabilities. Reference: Python's [tomllib documentation](https://docs.python.org/3.14/library/tomllib.html).
