# Ruling: attributed governance communication protocol

- **id:** `ruling-2026-08-29-attributed-governance-communication-protocol`
- **decided:** 2026-08-29
- **authority:** principal (decision), operator (directed that it be filed)
- **applies_to:** Sovereign Agent 1.x — all governance-bearing communication between seats, from this ruling forward
- **status:** ACTIVE

This ruling faithfully transcribes the Principal's decision to adopt an
attributed governance communication protocol, issued as a Principal `decision`
and directed by the Operator to be filed as a tracked ruling, with current state
explicitly reconciled at filing. It is transcribed here by the Sparring seat
under that Operator directive; transcribing a higher authority's decision is not
authoring it, and filing it is not a Sparring verdict on it (see "Provenance of
this file" at the end). It exists because the project repeatedly encountered
provenance failures — stale relays, misrouted reviews, unattributed verdicts,
and proposals presented as decisions — that a green gate cannot catch.

## Protocol text (verbatim)

The identification protocol is immediately operative for all future
governance-bearing communication in Sovereign Agent:

```text
FROM:
TO:
AUTHORITY:
MESSAGE TYPE: decision | proposal | request | evidence | verdict | status
SUBJECT:
BOUND TO: repository / PR / commit / review, when applicable
SOURCE: direct observation / message / durable URL or record
```

## Interpretation

* `FROM` identifies who authored the claim.
* `TO` identifies the intended recipients.
* `AUTHORITY` identifies the capacity in which the sender speaks.
* `MESSAGE TYPE` prevents a proposal, relay, or observation from resembling a ruling.
* `BOUND TO` is mandatory for exact-head reviews, acceptances, implementation claims, and audit results.
* `SOURCE` distinguishes firsthand verification from relayed content.

A message attributed to Sparring but delivered by Master must say that it is a
relay and cite the durable source. It does not become Sparring's verdict merely
because the prose resembles Sparring's voice.

## Authority boundaries

* Operator appoints seats, resolves organizational authority, and may direct or halt the overall undertaking.
* Principal decides scope, accepts or rejects implementation, resolves design forks, and authorizes progression between units.
* Master proposes, implements, verifies, files PRs, and executes authorized merges. Master does not issue Principal decisions or Sparring verdicts.
* Sparring independently reviews and issues exact-head verdicts. Sparring's approval is necessary where required but is not Principal acceptance.
* Stream seats implement bounded work and report evidence. They do not approve or merge their own work.

`Decision:` without Principal or Operator authority is not a decision. `APPROVED`
without authenticated Sparring provenance is not a review. A green gate is
evidence, not acceptance.

## Failure behavior

Missing, contradictory, or ambiguous attribution causes the message to be held
rather than executed.

The receiving seat must:

1. Check the filed record.
2. Identify the actual author and authority.
3. Resolve the bound repository, PR, SHA, review, or comment.
4. Treat unverifiable content on its technical merits only, explicitly as its own finding — not as the alleged sender's ruling.

No seat may silently infer provenance from tone, vocabulary, formatting, or
surrounding conversation.

## Historical record

Existing decisions, approvals, and acceptance records remain valid. They do not
need retroactive formatting when their provenance is already durable and
unambiguous.

## Current operative state (reconciled at filing)

This section WAS part of the Principal's decision message — the Principal's
message ended with a `Current operative state` section of five bullets. The
filer transcribed four of those five bullets unedited. The third bullet was
reconciled, not transcribed: the Principal's message said "PR #36 remains
pending Sparring review"; by the time this ruling was filed, that review had
already landed, and the filer updated the bullet to say so without flagging
the change as an edit rather than a transcription. That one silently-edited
bullet is the entire reason the "word for word" claim was false — durable
source: [PR #36 review `5058066389`](https://github.com/zeroemployeeorg/sovereign-agent/pull/36#pullrequestreview-5058066389),
`APPROVED` at exact head `cbeeca6f73ef44e47a8a2b5f2545406971dc2445`, submitted
`2026-08-29T12:25:36Z`, before this ruling was filed at `12:51:26Z`.

* Unit 9 implementation is merged at `f3db778d9391d8c1d081774e6b992a093d5a5bd5`.
* Its post-merge audit is `PASS`, with A-U9-2 addressed in PR #36.
* PR #36 is the reviewed status change from `PROPOSED` to `ACCEPTED` at
  `cbeeca6f73ef44e47a8a2b5f2545406971dc2445`, `APPROVED` by Sparring review
  `5058066389`.
* Unit 9 is not closed until that reviewed status change merges and is verified
  on `main`.
* Unit 10 remains unauthorized and unstarted.

## How to check this ruling against the repository

This is a process ruling: its subject is communication between seats, not code,
so no automated gate can confirm a given message obeyed it. The check is
behavioral and applies at the moment a governance-bearing message is received:

```text
# Every governance-bearing message carries the header block above.
# For any exact-head review, acceptance, implementation claim, or audit
# result, BOUND TO names a repository / PR / commit / review, and SOURCE
# distinguishes direct observation from a relay.
#
# On missing, contradictory, or ambiguous attribution: HOLD, do not execute.
# Then: check the filed record; identify the true author and authority;
# resolve the bound PR/SHA/review/comment; and treat unverifiable content
# on its technical merits only, as the receiver's own finding, never as the
# alleged sender's ruling.
```

The rulings index (`docs/rulings/index.md`) lists this file; `scripts/verify_curriculum.py`
enforces that the index and the directory agree, so this ruling cannot silently
drift out of the durable record it establishes the discipline for.

## Provenance of this file

`FROM:` Principal (decision); Operator (directive to file).
`AUTHORITY:` Principal decision, Operator-directed filing.
`MESSAGE TYPE:` decision, transcribed into a durable ruling.
`SOURCE:` the Principal's `decision` message relayed by the Operator in session.

Filed by the Sparring seat under the Operator's direct directive to file it.
Per this ruling's own authority boundaries and standing doctrine, Sparring does
not author-and-co-sign: this transcription is **not** a Sparring verdict on
itself. The merge-authorizing check — that the transcription is faithful to the
Principal's decision and the filing is well-formed — belongs to the Master or
Operator, not to a Sparring approval of its own filing.

### Correction (2026-08-29, same day): the original merge confirmation overclaimed

Master's merge-confirmation comment on PR #37, and the merge commit message
itself, stated that "current operative state all match word for word" against
the Principal's decision message — describing the ENTIRE filed document,
including the "Current operative state" section, as verbatim. That was false.
Only the protocol text itself (now "Protocol text (verbatim)" above) is
verbatim to the Principal's decision message. The "Current operative state"
section WAS part of that message; what was false was "word for word," because
the filer silently edited its `PR #36` bullet — from the Principal's own
"remains pending Sparring review" to "is the reviewed status change from
`PROPOSED` to `ACCEPTED`" — to reflect that Sparring's review had landed by
filing time, without marking that bullet as reconciled rather than
transcribed. That single edited bullet, not an invented section, is what made
"word for word" false. Caught and corrected same-day, additively: this
section's own heading now says "reconciled at filing," not "verbatim," the top
summary paragraph says "faithfully transcribed... with current state
explicitly reconciled," and the operative-state section states plainly that it
was part of the Principal's message and names exactly which bullet was edited
and why. The protocol text itself was never in question and remains unedited
above.

### Second correction (2026-08-29, same day): the first correction itself misstated the provenance it was correcting

The paragraph above, in its first filed form, overcorrected: it claimed the
"Current operative state" section "was never part of [the Principal's]
message" and that the filer "wrote" it — both false against the bytes.
Sparring's independent review of this PR (verdict `CHANGES_REQUESTED`, filed
against head `7e1d35b3`) caught this directly, comparing the Principal's
actual decision message against the filed ruling and the review timeline. The
accurate account, which now stands above and in the "Current operative state"
section itself: the section was genuinely present in the Principal's message,
five bullets; the filer transcribed four unedited and silently edited the
third (the `PR #36` bullet) to reflect a fact — Sparring's review having
landed — that postdated the Principal's own wording. That is a more
significant transcription deviation than inventing a section outright, not a
smaller one, and a provenance-accuracy ruling cannot round it off in the
filer's favor. Recorded here, additively, rather than silently rewritten,
matching the same discipline this correction itself exists to model.
