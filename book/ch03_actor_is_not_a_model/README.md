# Chapter 3 — The Actor Is Not the Model

## The bug that started an argument

Lucy runs an ice cream shop. This summer she started letting a language model help
with the boring part: watching stock and proposing reorders. One Saturday the
model proposed reordering **400 tubs of vanilla** — ten freezers' worth. It did
not go through, because in [Chapter 2](../ch02_work_needs_governance/README.md)
you built the governed check that re-reads reality before a proposal commits.

This chapter answers the question Lucy's friend asked that evening:

> "If you switch to a smarter model, does the shop get safer, or more dangerous?"

The honest answer is **neither**, by design — and the reason is the most important
idea in this book. Most systems that bolt an LLM onto a business get it exactly
backwards: they tie *authority* to *intelligence*, so a sharper model quietly
gets a longer leash. In a Sovereign Agent, the model is a **swappable part of an
actor**, and the actor's authority comes from its **role**, not from the model
behind it. You will build that distinction from the real production pieces, swap
the model, and prove that who-may-do-what did not move an inch.

## Learning objective

Understand why swapping the intelligence behind an actor changes its *proposals*
but not its *authority*, and why a provider therefore cannot approve its own work.
You will build the real actor representation (an actor **has** a `provider`
field), the real role-to-authority policy, and the real rebind, and see that
authority is enforced by a role lookup — not by a model, a prompt, or a clever
data-structure trick.

## What you'll learn

- That in production an actor **has** a `provider` — the swappable intelligence
  lives on the actor, alongside its `role` and `authority`.
- That authority safety comes from a **role → allowed-actions** policy table, not
  from making an object immutable.
- Why the actor whose model *did* the work still cannot *accept* it, no matter
  which model you bind to it.

**Prerequisites:** Chapters 0–2. Comfort with Python classes and `pydantic`
models. No machine-learning background required.

## The tempting mistake, built and broken

The intuitive design ties power to smartness: a good-enough model earns the right
to sign off on its own decisions. Let's build that and watch it fail. Here is an
actor whose authority is just "whatever its model is allowed to do," handed in
per call:

```python
def approve(outcome_id, approver_can_accept):
    if approver_can_accept:
        print(f"accepted {outcome_id}")
    else:
        raise PermissionError("not allowed")


# The operator's model is sharp today, so we trust it to accept its own work:
approve("out_vanilla", approver_can_accept=True)
```

This "works," and it is a disaster. `approver_can_accept` is a claim the caller
makes about itself; a capable model will happily claim it. Authority that travels
as a boolean argument is authority the worker can grant itself. The fix is to
stop asking the caller and start looking authority up — from the actor's **role**.

## The real actor: the model lives *on* it

In production an actor is a small typed record. Crucially, the `provider` — the
swappable intelligence — is a field **on the actor**, right next to its `role`
and its capability list. (This mirrors `sovereign_agent.models.Actor`.)

```python
from pydantic import BaseModel


class Actor(BaseModel):
    id: str
    role: str
    provider: str  # the swappable intelligence: "scripted", "claude", "ollama", ...
    authority: list[str]  # the provider-facing capabilities this actor carries


operator = Actor(
    id="lucy-operator",
    role="operator",
    provider="scripted",
    authority=["read", "write_workspace", "run_checks", "report"],
)
```

Notice what is *not* in that authority list: `accept`. Hold onto that — it is the
hinge the whole chapter turns on. Note too that the actor is an ordinary mutable
model. Its safety will not come from freezing it; it will come from where
authority is actually decided.

## Authority is granted by role, not by the model

Here is the real source of authority: a table mapping each role to the actions it
may take. (This mirrors `ROLE_AUTHORITY` in `sovereign_agent.policy`.)

```python
ROLE_AUTHORITY = {
    "principal": {"define_outcome", "accept", "grant_exception", "rule"},
    "master": {"plan", "assign", "integrate", "request_ruling"},
    "operator": {"read", "write_workspace", "run_checks", "report"},
    "sparring": {"read", "review", "rule"},
    "verifier": {"run_checks", "record_evidence"},
}


def require_authority(role, action):
    if action not in ROLE_AUTHORITY[role]:
        raise PermissionError(
            f"Role {role} attempted {action}. "
            "Authority is granted by role, not by a provider or a prompt."
        )
```

That refusal message is the thesis of the chapter, in the production code itself:
**authority is granted by role, not by a provider or a prompt.** The `operator`
role's actions are `read`, `write_workspace`, `run_checks`, `report`. `accept` is
not among them — and no model can add it, because the model is not consulted here
at all.

## Rebinding: change the mind, record the act, keep the authority

Swapping the model is changing the actor's `provider` field. It is a governed act:
only an actor whose role may `rule` can do it, and it is written to the ledger as
an event. (This mirrors `Organization.rebind_actor`.)

```python
event_log = []


def rebind_actor(actor, new_provider, performed_by):
    require_authority(performed_by.role, "rule")  # only principal/sparring may rule
    old = actor.provider
    actor.provider = new_provider  # mutate the field ON the actor
    event_log.append(
        {"kind": "actor.provider_rebound", "actor": actor.id, "from": old, "to": new_provider}
    )


principal = Actor(id="lucy", role="principal", provider="n/a", authority=["accept", "rule"])

rebind_actor(operator, "ollama", performed_by=principal)
print("provider:", operator.provider)
print("role:", operator.role, "| authority:", operator.authority)
```

```text
provider: ollama
role: operator | authority: ['read', 'write_workspace', 'run_checks', 'report']
```

We replaced a deterministic stand-in with a real local model. `operator.provider`
changed; its `role` and `authority` did not. The mind changed; the identity did
not — and the change is now a row in `event_log`, not a quiet edit.

## Why a provider cannot approve its own work

Now the payoff. Try to let the operator accept, however sharp its new model is:

```python
try:
    require_authority(operator.role, "accept")
except PermissionError as error:
    print("refused:", error)

rebind_actor(operator, "claude", performed_by=principal)  # an even better model
try:
    require_authority(operator.role, "accept")
except PermissionError as error:
    print("still refused after the upgrade:", error)
```

```text
refused: Role operator attempted accept. Authority is granted by role, not by a provider or a prompt.
still refused after the upgrade: Role operator attempted accept. Authority is granted by role, not by a provider or a prompt.
```

The operator role cannot accept, and swapping in a smarter model does not change
that, because the check never looks at the model. Acceptance belongs to the
`principal` role. There is a second guard behind it — the organization also
refuses acceptance from whoever *performed* the work, deriving the performer from
the assignment ledger rather than trusting a caller-supplied name — so even a
principal cannot rubber-stamp work they personally did. Together: **accountability
lives on the role, so upgrading the model can never launder a proposal into an
approval.**

## The exercise

Confirm all of this in the *real* organization, where `Actor`, `ROLE_AUTHORITY`,
and `rebind_actor` are the production versions of what you just built:

```bash
python book/ch03_actor_is_not_a_model/solution.py --root /tmp/lucy-ch03 --provider ollama
```

`solution.py` runs one assignment, rebinds `operator-course`'s provider, runs
another, and reports whether the actor's identity survived. (Use `--provider
scripted` if you have no local model; with a real one, `export
SOVEREIGN_AGENT_LLM_MODEL=qwen3` first — the built-in `ollama` provider ships in
sovereign-agent 1.1.0.)

## Expected observations

The exercise prints a JSON summary. The line that matters:

```text
"identity_unchanged": true
```

Before and after the rebind, `operator-course` keeps the same id, role, and
authority; only `provider` changed. Confirm the governed record of the change:

```bash
sqlite3 /tmp/lucy-ch03/.sovereign/organization.db \
  "SELECT kind FROM events WHERE kind = 'actor.provider_rebound';"
```

Expected: one row. Rebinding is an act the organization records, performed by an
actor whose role may `rule` — not a config edit that happens quietly. If a live
CLI is missing or cannot prove its required flags, you will see a refusal instead
of a run. That is the correct outcome: an unprovable capability fails closed.

## Edge cases and failure modes

| What you try | What happens | Why |
| --- | --- | --- |
| An actor without `rule` authority rebinds a provider | Refused by `require_authority` | Swapping intelligence is a governed decision, reserved to ruling roles |
| The operator tries to `accept` | Refused, by role, regardless of model | `accept` is not in the operator role's action set |
| A principal tries to accept work they performed | Refused by the no-self-approval guard | The performer is read from the ledger, not supplied by the caller |
| A provider exits `0` but writes no report | The receipt is rejected | Silence is not success |

## Common mistakes

- **Storing authority as a fact the caller asserts** (a boolean, a token in the
  prompt). Then the worker grants itself power. Look authority up from the role.
- **Using object immutability as a security boundary.** A `frozen` model stops a
  stray assignment, not an attacker, and it is not why acceptance is safe here.
  The role policy is.
- **Believing a better model deserves a longer leash.** A more capable provider
  proposes more capably-wrong actions. The guardrails are on the role precisely
  so they do not move when the model does.

## Exercises

1. Add a `verifier` actor and confirm `require_authority("operator", "record_evidence")`
   is refused while `require_authority("verifier", "record_evidence")` passes.
2. Extend `rebind_actor` to also refuse an unknown provider name (one not in a set
   of known providers), and show the actor's `provider` is unchanged after the
   refusal.
3. **(Stretch)** In two sentences, explain why moving `provider` *off* the actor
   into a separate table would be a genuine architecture change requiring its own
   design decision — not something a chapter can simply assert.

<details>
<summary>Solutions</summary>

1. `record_evidence` is in the `verifier` role's set but not the `operator`'s, so
   the first call raises and the second does not.
2. Check membership before mutating: `if new_provider not in KNOWN: raise
   PermissionError(...)`, placed before `actor.provider = new_provider`, so a
   refusal leaves the field untouched.
3. Production stores the provider on the actor and `rebind_actor` mutates it in
   one place; a separate binding table would change the data model, the migration,
   and every read path — a real design change with its own trade-offs, not a
   detail prose can wave into existence.
</details>

## Learner verification command

```bash
python -m pytest tests/test_actors_and_mailbox.py tests/test_providers.py -q
```

Expected: all pass. These prove actor identity survives a provider rebind, that
authority is enforced by role, and that adapters build argument arrays rather than
shell strings.

## Summary

- An **actor** carries its swappable `provider` as a field, alongside its `role`
  and `authority`. The model lives on the actor; it is not the actor.
- **Rebinding** changes `provider`, is reserved to ruling roles, and is recorded
  as an event. Identity — id, role, authority — is untouched: `identity_unchanged: true`.
- **Authority is granted by role**, through a role→actions policy, enforced by
  `require_authority`. The operator role cannot `accept`, and no model changes that.
- Because accountability lives on the role, **upgrading the model changes the
  proposals but never the rules** — the answer to Lucy's friend.

## Explain it back

1. In production, where does an actor's `provider` live — on the actor, or in a
   separate table? What did rebinding actually change in the exercise?
2. The chapter's toy first tried to gate acceptance on a boolean the caller
   passes. What attack does that enable, and how does the role lookup close it?
3. `require_authority` never looks at the actor's `provider`. Why is that the
   whole point of this chapter?
4. The operator role's actions are `read`, `write_workspace`, `run_checks`,
   `report`. Which role has `accept`, and why is that separation not mere
   bureaucracy?
5. Why is object immutability (`frozen`) the *wrong* explanation for why the
   operator cannot approve its own work?
6. `operator-course` is rebound from `scripted` to `ollama`. Who is accountable
   for the next restock it proposes, and how would you show that from the ledger?

Next: [Chapter 4 — Work stays inside its boundary](../ch04_work_stays_inside_its_boundary/README.md)
