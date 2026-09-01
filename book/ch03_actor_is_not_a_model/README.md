# Chapter 3 — The Actor Is Not the Model

## The bug that started an argument

Lucy runs an ice cream shop. It is a small shop — six flavors, one freezer, one
laptop — but it is busy, and this summer she started letting a language model
help with the boring part: watching stock and proposing what to reorder.

One Saturday the model proposed reordering **400 tubs of vanilla**. The freezer
holds forty. If that order had gone through, Lucy would have spent the month's
rent on ice cream that would melt on the sidewalk before she could sell it.

It did not go through. In [Chapter 2](../ch02_work_needs_governance/README.md)
you built the piece that said *no* — the governed check that re-reads reality
before it lets a proposal commit. This chapter is about a subtler question, the
one Lucy's friend asked her that evening:

> "If you switch to a smarter model, does the shop get safer, or more dangerous?"

The honest answer is **neither** — and understanding *why* is the most important
idea in this book. Most systems that bolt an LLM onto a business get this exactly
backwards: they treat "which model" and "what it is allowed to do" as the same
knob. Turn up the intelligence and you turn up the authority. That is how a
sharper model becomes a more expensive mistake.

By the end of this chapter you will be able to swap the intelligence behind
Lucy's shop — from a dumb scripted stand-in to a real local model — watch its
proposals change completely, and **prove that who is allowed to do what did not
move an inch.**

## Learning objective

Understand why swapping the intelligence behind an actor does not change who is
accountable — and why a provider therefore cannot approve its own work. You will
build the actor/provider distinction from first principles, then confirm it in
the production organization: an actor keeps its `id`, `role`, and `authority`
across a provider rebind, and acceptance is refused for whoever performed the
work, no matter which model is bound to them.

## What you'll learn

- The difference between an **actor** (a governed identity) and a **provider**
  (a swappable intelligence), and why welding them together is the root defect.
- How the organization records a provider change as a *governed act*, not a
  quiet config edit.
- Why the thing that *proposed* a piece of work can never be the thing that
  *approves* it — and how that is enforced by code that reads the ledger, not by
  anyone's good intentions.

**Prerequisites:** Chapters 0–2. Comfort with Python functions, dictionaries,
and `dataclasses`. No machine-learning background required.

## An analogy you already understand

Think about the cash register at Lucy's shop.

The **register** has rules: it records every sale, it needs a manager's key to
void a transaction, it prints a receipt. Those rules do not care *who* is
standing at it. A new hire, a twenty-year veteran, or Lucy herself — the register
treats them all the same, because the rules belong to the *role*, not the person.

The **person** at the register is replaceable. Hire a sharper cashier who scans
faster and upsells better, and the shop gets a better *cashier*. It does not get
a register that suddenly lets cashiers void their own transactions.

An **actor** is the register: a governed identity with a role and a fixed set of
permissions. A **provider** is the person: the intelligence doing the thinking,
hired and swappable. "Upgrading the model" is hiring a sharper cashier. It is
*not* rewriting the register's rules — and if it ever *did*, that would be a bug
so dangerous it is the whole reason this chapter exists.

Hold that picture. Now let's build it, starting from the naive version so you can
feel exactly where it breaks.

## Building the actor (and the trap)

Start with identity. An actor needs an id, a role, and a set of things it may do:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Actor:
    id: str                      # "lucy-operator", stable forever
    role: str                    # "operator", "verifier", "principal"
    authority: frozenset[str]    # what this actor may do
```

We made it `frozen=True` on purpose. An actor's identity must not be editable by
a stray line of code that happens to hold a reference to it. Changing what an
actor *is* should go through a governed operation that records the change — which
we will build in a moment.

Here is the actor that runs Lucy's restock work:

```python
operator = Actor(
    id="lucy-operator",
    role="operator",
    authority=frozenset({"propose_restock", "write_workspace"}),
)
```

Read what `lucy-operator` may do: it may **propose** a restock and write to its
scratch workspace. It may **not** approve work — that permission simply is not in
the set. Hold onto that; it is the hinge the whole chapter turns on.

Now, where does the *thinking* happen? Behind the actor, in a provider. The
naive design — the one that causes the bug Lucy's friend worried about — is to
bake the provider *into* the actor:

```python
# DON'T do this — it welds identity to intelligence
@dataclass
class Actor:
    id: str
    role: str
    authority: set[str]
    provider: str      # <-- the trap
```

Why is this a trap? Because now "change the model" and "change who this actor is"
are the *same edit*. A function that swaps the provider is one typo away from
also touching the role or the authority. The dangerous change and the harmless
change live in the same place, guarded by the same (or no) review. Good systems
keep dangerous operations far away from routine ones.

So we store the binding *outside* the actor, in a small table the organization
owns:

```python
# which provider is currently behind each actor id
provider_bindings: dict[str, str] = {"lucy-operator": "scripted"}
```

The actor stays frozen and pristine. The binding is a separate, mutable fact.

## Rebinding: change the mind, keep the identity

Here is the operation that hires a sharper cashier. Read it, then we will walk
through the two things that make it safe.

```python
def rebind_provider(bindings, actor, new_provider, performed_by):
    # 1. Only an actor with ruling authority may rebind.
    if "rule" not in performed_by.authority:
        raise PermissionError(
            f"{performed_by.id} (role {performed_by.role}) may not rebind providers"
        )
    # 2. Return a NEW bindings table; never mutate the actor's identity.
    updated = dict(bindings)
    updated[actor.id] = new_provider
    print(f"event: actor.provider_rebound  {actor.id}: "
          f"{bindings.get(actor.id)} -> {new_provider}  by {performed_by.id}")
    return updated
```

Two properties make this safe, and both are worth saying out loud:

1. **Rebinding is a privileged act, not a config edit.** The function refuses to
   run for just anyone — `performed_by` must carry `"rule"` authority. Swapping
   the model is a *decision*, made by someone accountable. In Lucy's shop that is
   the principal (Lucy herself), never the worker whose model is being swapped.

2. **The actor object is never touched.** We copy the table and change one entry.
   The `Actor` — its id, role, authority — comes out the far side byte-for-byte
   identical, because it is literally the same frozen object. The *mind* changed;
   the *identity* did not. And notice the function prints an **event**: the change
   is recorded, not whispered.

Run it:

```python
principal = Actor("lucy", "principal", frozenset({"rule", "accept"}))

before = provider_bindings["lucy-operator"]
provider_bindings = rebind_provider(provider_bindings, operator, "ollama", principal)
after = provider_bindings["lucy-operator"]

print("provider:", before, "->", after)
print("identity unchanged:", operator.authority == frozenset({"propose_restock", "write_workspace"}))
```

```text
event: actor.provider_rebound  lucy-operator: scripted -> ollama  by lucy
provider: scripted -> ollama
identity unchanged: True
```

Read that last line again. We just replaced a deterministic fake with a real
local model. The proposals from `lucy-operator` will now be smarter, wordier,
occasionally surprising. And the answer to "who is `lucy-operator`, and what may
it do?" did not change at all. The register stayed the register while a better
cashier stepped up to it.

## The second half: you cannot approve your own work

There is a reason we kept `"accept"` *out* of the operator's authority. Make it
concrete. In Lucy's shop, work flows like this: the operator **proposes** a
restock, then — separately — a verifier checks the freezer and a principal
**accepts**. Proposal and approval are done by *different actors*. That is not
bureaucracy; it is the only thing standing between Lucy and a model that says "I
ordered 400 tubs, and I also confirm that was an excellent decision."

Here is a naive approval with the hole left in:

```python
def approve(outcome_id, approver):
    if "accept" not in approver.authority:
        raise PermissionError(f"{approver.id} may not accept")
    print(f"event: outcome.accepted  {outcome_id}  by {approver.id}")
```

This checks that the approver *may* accept — good, but not enough. It does not
check that the approver **is not the same actor that did the work.** The fix is
to derive the *performers* from the ledger — the recorded list of who actually
did the work — and refuse approval from any of them:

```python
def approve(outcome_id, approver, performers):
    if "accept" not in approver.authority:
        raise PermissionError(f"{approver.id} may not accept")
    if approver.id in performers:
        raise PermissionError(f"{approver.id} performed this work and may not approve it")
    print(f"event: outcome.accepted  {outcome_id}  by {approver.id}")
```

Two properties matter enormously here, and they connect straight back to the
first half of the chapter:

- **`performers` comes from the ledger, not from the caller.** We do not *ask*
  who did the work; we *look it up* from the durable record of assignments. A
  caller cannot lie about it to sneak an approval through.
- **This check is about the actor, and actors do not change when models do.**
  Because the performer list is a set of *actor ids*, swapping `lucy-operator`'s
  provider from `scripted` to `ollama` to `claude` changes nothing here. The
  intelligence that did the work still cannot bless it, however smart it gets.

That is the whole thesis in one sentence: **accountability lives on the actor,
so upgrading the model cannot launder a proposal into an approval.**

## The exercise

You have built the idea by hand. Now confirm it in the *production* organization,
where the same rules are enforced for real. `solution.py` uses the real
`Organization`, the real provider registry, and the real rebind.

1. Inspect `operator-course` in `sovereign.toml`. Record its id, role,
   authority, and provider.
2. Run the exercise with a provider you have installed. Since sovereign-agent
   1.1.0, the built-in `ollama` provider works with a local model — no cloud, no
   key:

   ```bash
   ollama pull qwen3
   export SOVEREIGN_AGENT_LLM_MODEL="qwen3"
   python book/ch03_actor_is_not_a_model/solution.py --root /tmp/lucy-ch03 --provider ollama
   ```

   (You can also pass `--provider claude`, `codex`, or `cursor` if you have that
   CLI. With no live provider at all, read the refusal — that is a valid result.)
3. Inspect the first scripted receipt under
   `/tmp/lucy-ch03/.sovereign/runs/*/receipt.json`.
4. Find the governed `actor.provider_rebound` event. The principal changed the
   provider binding; the actor's id, role, and authority did not move.
5. Replace `ollama` with another provider and run again. Watch the proposals
   change and the governance stay exactly where it was.

## Expected observations

The exercise prints a JSON summary. The line that matters:

```text
"identity_unchanged": true
```

Before and after the rebind, `operator-course` keeps the same id, the same role,
and the same authority. Only the provider binding changed. Confirm the governed
record of that change:

```bash
sqlite3 /tmp/lucy-ch03/.sovereign/organization.db \
  "SELECT kind FROM events WHERE kind = 'actor.provider_rebound';"
```

Expected: one row. Rebinding is an act the organization records, performed by an
actor with ruling authority — not a config edit that happens quietly. If a live
CLI is missing or cannot prove its required flags, you will see a refusal instead
of a run. **That is the correct outcome:** capability claims come from probing
the installed provider, and an unprovable capability fails closed.

## Edge cases and failure modes

A governed system is defined as much by what it refuses as by what it does. Watch
for these:

| What happens | What the organization does | Why |
| --- | --- | --- |
| A live CLI is not installed | Refuses the run, names the missing capability | Fail closed: an adapter may not hard-code an unsupported flag |
| A provider exits `0` but writes no `report.json` | Rejects the receipt | Silence is not success; the work claim must be present and valid |
| A provider returns malformed JSON | Fails the receipt | A record you cannot parse is not evidence |
| Someone passes an empty performer set to `approve` | Approval slips through *in the toy* | Exactly why the real performer set is read from the ledger, never from the caller |

That last row is the one to internalize. In your hand-built version, an empty
`performers` set would let a worker approve itself by lying that it did nothing.
The production organization does not accept the performer list as an argument at
all — it derives it from the recorded assignments. The attack is not defended
against; it is made *unrepresentable*.

## Break it and watch it fail

Belief is cheaper than proof. Open a Python shell and try to smuggle `accept`
onto the worker by editing its authority directly:

```python
operator.authority = frozenset(operator.authority | {"accept"})
```

```text
dataclasses.FrozenInstanceError: cannot assign to field 'authority'
```

The actor is frozen — you cannot quietly grant it a new power. The only way to
change what an actor may do is through a governed operation that *records* the
change, exactly as `rebind_provider` records a rebinding. There is no back door,
because we removed the door on purpose.

## Learner verification command

```bash
python -m pytest tests/test_actors_and_mailbox.py tests/test_providers.py -q
```

Expected: all pass. These prove actor identity survives a provider rebind, that
authority cannot be self-granted, and that adapters build argument arrays rather
than shell strings.

## Common mistakes

- **Storing the provider on the actor.** The single most common design error. It
  welds the dangerous operation (change identity) to the routine one (change
  model). Keep the binding in a table the organization owns.
- **Trusting the caller for the performer list.** If `approve` accepts
  `performers` from whoever calls it, a caller can pass an empty set and approve
  anything. Derive performers from the recorded ledger.
- **Thinking a smarter model needs fewer guardrails.** It needs the same ones. A
  more capable provider proposes more capable *and* more capably-wrong actions.
  The guardrails are on the actor for exactly this reason.

## Exercises

1. **Add a role.** Create a `verifier` actor with authority `{"verify"}` and a
   `verify(outcome_id, verifier)` that refuses any actor lacking `"verify"`.
   Confirm `lucy-operator` cannot verify its own restock.
2. **Log the rebind.** Extend `rebind_provider` to append a record to a
   `ledger: list[dict]` with the actor id, old provider, new provider, and who
   performed it; assert the ledger contains exactly one `provider_rebound` entry
   after one rebind.
3. **(Stretch)** Explain in two sentences why `approve(outcome, principal,
   performers=set())` is dangerous, and where the real `performers` must come
   from so that call is impossible to make.

<details>
<summary>Solutions</summary>

1. `verify` mirrors `approve`'s authority check:
   `if "verify" not in verifier.authority: raise PermissionError(...)`. Since
   `lucy-operator`'s authority is `{"propose_restock", "write_workspace"}`, it
   fails the check.
2. Append `{"kind": "provider_rebound", "actor": actor.id, "from":
   bindings.get(actor.id), "to": new_provider, "by": performed_by.id}` inside the
   function; assert `sum(e["kind"] == "provider_rebound" for e in ledger) == 1`.
3. An empty set means nobody is recorded as a performer, so the "you cannot
   approve your own work" check passes vacuously — a worker could approve itself
   by claiming it did nothing. The performer set must be derived from the durable
   assignment ledger inside the approval path, never accepted as a caller
   argument.
</details>

## Summary

- An **actor** is a governed identity — id, role, authority. A **provider** is
  the swappable intelligence behind it. Keep them in separate places.
- **Rebinding** the provider is a privileged, recorded act that changes the mind
  and leaves the identity untouched. You proved it: `identity_unchanged: true`.
- **Approval is refused for performers**, and performers come from the ledger,
  not the caller — so the thing that did the work can never bless it.
- Because accountability lives on the actor, **upgrading the model changes the
  proposals but never the rules.** That is why the answer to Lucy's friend is
  "neither safer nor more dangerous, by design."

## Explain it back

Answer in your own words before moving on. If you cannot, re-read the
observations above — the answers are all visible in the database.

1. In the cash-register analogy, which part is the actor and which is the
   provider? What real failure does keeping them separate prevent?
2. Why is a provider session id evidence about continuity but not about actor
   identity?
3. What should happen if a CLI exits zero but omits its terminal event or
   `report.json`?
4. Why may an unknown valid event be retained while malformed JSON must fail the
   receipt?
5. In your own words: what is the difference between an actor and a provider?
6. `operator-course` is rebound from `scripted` to `ollama`. Who is accountable
   for the next restock it proposes, and how would you show that from the ledger?
7. Why does deriving the performer from assignments — rather than accepting it as
   an argument — matter for keeping a provider from approving itself?

Next: [Chapter 4 — Work stays inside its boundary](../ch04_work_stays_inside_its_boundary/README.md)
