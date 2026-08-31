# Principal handover — sovereign-agent (Sparring-compiled reconstruction)

**Compiled by:** Sparring (sovereign-agent seat), 2026-08-31, at `main = a17a01a6926168234ebf9622076ac2cf258da5ed`.
**Purpose:** the prior Principal was lost. This equips a newly-seated local Principal with the governance context, pending decisions, doctrine, protocol, and review standard that are otherwise ephemeral.

## 0. What this document is — and is NOT

- It is a **faithful reconstruction** by the Sparring (independent-review) seat.
- It is **NOT a ruling, NOT new authority, and NOT a decision on anything still open.** Sparring cannot make Principal decisions; nothing here creates them.
- The **authoritative durable record** is the merged rulings (`docs/rulings/`) and SOWs (`docs/sows/`) plus the per-unit acceptance records (`docs/v1-unit*.md`) and the PR history. Where this document reconstructs the prior Principal's *ephemeral reasoning or decisions not captured in-repo*, the new Principal should **verify against those durable artifacts and re-affirm before relying on it.**
- Trust order when anything here disagrees with the repo: **repo wins.**

## 1. The project in one paragraph

Sovereign Agent 1.x is an **approachable executable textbook and reference implementation** in Python — an educational local artifact, not production software. Persistence is **SQLite** (stdlib, no server, one inspectable file; runs on a student laptop). It must remain fully teachable without any credentialed provider. A real 30-day operational deployment pilot is **NOT** part of this textbook — it belongs to the successor runtime **ZEO Go**. This framing was an Operator correction (message id `SA-P-20260830-UNIT11-LOCAL-001`) and is now ruled.

## 2. The Principal role and its authority boundaries

- Principal = **scope and acceptance authority**. Rules on scope questions; accepts SOWs and implementations **at exact commit heads**; authorizes each terminal act with its own separate, explicit decision.
- **Acceptance arrives as a message, never as a gate or side-effect.** Merging a PR never constitutes acceptance.
- The Principal **does not merge** (that is Master's act) and does not author-then-co-sign.
- **Multi-gate discipline** (rigorously enforced this project): SOW-merge ≠ implementation authorization ≠ each terminal-act authorization ≠ closure. Each gate is a distinct decision **bound to an exact commit SHA**.
- Seats: **Master** (structure/sequencing/merges/authors rulings & SOWs, spawns streams), **Sparring** (independent review; co-signs or withholds at exact heads; never merges), **Stream/little-Claude** (executes one scope), **Operator** (human principal-of-principals), **Principal** (this seat).

## 3. Mandated communication protocol (Operator directive `msg_01a053b0-1d8c-78a6-a2f0-55c97ef27b14`, 2026-08-30, effective immediately)

Every organizational message carries this envelope:

```
FROM:
TO:
CC:                # optional
AUTHORITY:
MESSAGE TYPE:      # one of the controlled types below
MESSAGE ID:        # msg_<uuid>, minted once, never reused
CREATED AT:        # absolute UTC timestamp
CORRELATION ID:    # groups a workflow/thread (required for ongoing work)
CAUSATION ID:      # the exact message this responds to (required when responding)
SUPERSEDES ID:     # only for a correction/replacement
BOUND TO:          # exact SHA / PR / artifact / decision where applicable
SUBJECT:
```
…and ends with `ECHO: <exact MESSAGE ID>` (must match `MESSAGE ID`).

- **Identifier:** target is `msg_<uuidv7>`; during bootstrap a lowercase OS uuid is accepted (`printf 'msg_%s\n' "$(uuidgen | tr '[:upper:]' '[:lower:]')"`). Mint once; never reuse; never derive one from another; chronological ordering is not authority.
- **Controlled types (use the narrowest):** DECISION, REQUEST, EVIDENCE, VERDICT, OCCUPANCY, HEARTBEAT, INCIDENT, CORRECTION, ACKNOWLEDGMENT.
- **Body:** lead with OUTCOME, then EVIDENCE / REQUIRED NEXT ACTION (name its owner) / DEADLINE OR CHECKPOINT / CURRENT STATE / OPERATOR ACTION. Any message CC'd to the Operator states `OPERATOR ACTION:` (often `None`).
- **Duplicates & corrections:** dedupe by `MESSAGE ID`; a correction is always a **new** message with `SUPERSEDES ID` (never a silent edit); receiving the same message via another channel does not make it new.
- **Relay:** a transport relay preserves the original `MESSAGE ID`/body/ECHO verbatim; the **Operator must not be the routine seat-to-seat relay**. "Sent" ≠ "delivered."
- No current implementation scope is expanded by this directive; the Steward incorporates it into the architecture/rulings packet.

There is also an earlier, related ruling: **`docs/rulings/2026-08-29-attributed-governance-communication-protocol.md`** (attribution headers; hold on ambiguous attribution; no silent provenance inference). The envelope directive above extends that discipline.

## 4. Current governance state (durable, at `main = a17a01a`)

**Rulings (all in `docs/rulings/index.md` — the index guard fails the curriculum gate if it drifts):** educational-reset; main-is-the-1x-line; conditional-effects amendment; unit4-fencing deferral; **unit6-smokes→Unit12 deferral**; one-process-per-actor; outcomes-are-conditions/SOWs-are-work; persistence-boundary-refinement; sqlite-writers-inside-boundary; **book-publication-destination** (book is published by `zeo-site`; this repo builds no site); unit7-is-workspaces-not-pulse; unit9-pulse-separate-from-supervisor; **attributed-governance-communication-protocol**; **unit11-scope**; **unit11-local-closure-supersedes-real-deployment-gate**; **unit12-scope**.

**Units:**
- **Units 0–11: complete/accepted.** Per-unit acceptance records: `docs/v1-unit7…11-*.md` all `ACCEPTED`.
- **Unit 11 closed on the local-SQLite basis.** The real-deployment pilot-start gate was **withdrawn** (supersession ruling `2026-08-30-unit11-local-closure-supersedes-real-deployment-gate.md`). No real 30-day pilot occurred or is required. The execution packet and its four reserved identifiers (`sovereign-store-pilot-001`, etc.) are **retired unused** and must **never** be cited as evidence a pilot began. The pilot-start *mechanism* (`src/reference_organizations/store/pilot.py`, `start_pilot`) stands, exercised only against disposable `book-ch12-exercise-*` identities.
- **Unit 12: in progress.** Scope ruling merged (`2026-08-31-unit12-scope.md`); SOW merged (`docs/sows/sovereign-agent-v1-unit12-release-evaluation.md`, `status: PROPOSED`); **implementation PR #49 is Sparring-APPROVED at `e58eae713926b1a71a4871c21b39370113fa7a9c`** and awaits Principal acceptance (see §5).
- **Top-level design memo** (`…-educational-control-plane.md`): `status: DESIGN`. Its `done_when` line "30-day Sovereign Store pilot → redacted proof pack accepted" is **superseded** by "local, learner-controlled Sovereign Store release evaluation → redacted Unit 12 proof pack accepted" (Unit 12 scope ruling Holding 1); the additive correction note to that memo is a Unit 12 implementation deliverable landing with PR #49.

## 5. PENDING DECISIONS THE NEW PRINCIPAL OWES NOW — these are OPEN; Sparring has NOT decided them

**(a) PR #49 — Unit 12 implementation — acceptance.**
- Sparring co-sign: **APPROVED** at exact head `e58eae7…`. Independently verified: both gates by Sparring (pytest 358/9 deselected, curriculum twice, and the heavy `verify_release_candidate.py` all 6 stages incl. installed-wheel isolation); an in-process proof-pack mutation battery (every required rejection class caught; the real 40-hex/64-hex SHAs/digests that broke the SOW twice now correctly pass; name-alone/redaction not false-positived); `src/sovereign_agent/` untouched (budget `6208/6250`); manifest honest (all providers `NOT_RUN_UNAUTHENTICATED`, `release_candidate_commit: null`).
- **The Principal must decide acceptance** (a message, bound to `e58eae7…`), together with (b).

**(b) The M10 scope question (surfaced by Sparring; Principal's to decide).**
- The proof-pack `NOT_RUN`-means-PASS lie-detector (`scripts/verify_proof_pack.py`) runs **only** in provider-row context. A fabricated "the live evaluation passed / verified live" claim placed in `andrea_live_evaluation`'s free text while its `status` stays `"NOT_RUN"` **passes the verifier** — demonstrated concretely. A matching lie in a provider row **is** caught.
- **Not a literal violation:** the SOW rule targets values matching `NOT_RUN_*` (defined as exactly the two provider statuses); the andrea field uses bare `"NOT_RUN"`. So the verifier is literally compliant and every acceptance condition is met — which is why Sparring did **not** block. But it defeats the evident "anywhere in the manifest" intent (SOW §1) in an honesty-critical spot, and the andrea `status` is currently unvalidated.
- **Sparring's recommendation (advisory):** require the success-claim check to apply to any NOT_RUN-family status value (andrea included) and constrain the andrea `status` to a defined allowed set. **The Principal decides** whether to require this before accepting, or to accept as-is.

**(c) The remaining Unit 12 terminal gates — each a separate, later Principal act, in this order (Unit 12 scope Holding 5 / SOW "Final Unit 12 closure conditions"):**
1. Implementation acceptance (a/b above) → then separate implementation is already authorized and merged into PR #49; acceptance is what is pending.
2. The **Andrea live evaluation** — a real human session using `docs/andrea-chapters-0-12-evaluation.md` (pass ≥17/20, no zero on Tasks 2/7/8/9/10, first outcome ≤10 min, session ≤60 min). Separate authorization; participant selection may be an Operator act.
3. **`1.0.0rc1` → TestPyPI**, then the **redacted proof pack** filed, Sparring-verified (technically) and Principal-accepted as a release candidate.
4. **Final `v1.0.0`**: separate Principal authorization → tag → trusted-publisher PyPI publish → external verification → install-doc correction. **Final release comes BEFORE closure** (ordering was a defect the prior Principal caught; do not invert it).
5. **`PROPOSED → ACCEPTED`** flip (separate reviewed change) → clean-`main` gate → **Unit 12 closed**.
- Merging PR #49 authorizes none of 2–5. Each is its own decision bound to an exact commit.

## 6. Doctrine the prior Principal established (the "why", so it is not re-litigated blindly)

- **Append-only / never silently rewrite history.** Supersede via a new dated ruling; annotate superseded passages with additive correction notes that name the superseded text, state the replacement, and cite the ruling; the original text stays intact. (Applied to amendment 6, `done_when`, the SOW/ruling corrections.)
- **Educational-artifact decision** (SQLite; no production deployment to close a unit; ZEO Go owns the real pilot; **no DuckDB**).
- **Multi-gate authorization model** (§2, §5c).
- **Exact-head binding + zero-drift verification.** Every co-sign binds to a SHA and goes stale on any head change; every merge is confirmed byte-identical to the co-signed head before it is trusted.
- **Independent falsification.** Master and Sparring each reproduce findings and run mutation checks with *landed* mutations rather than trusting reports; probe the dual of every fix; verify citations to the bytes; cross-reference ordering/completeness against the governing authority and contracts against their actual inputs.
- **Honesty of evidence:** `NOT_RUN` never means `PASS`; providers without `LIVE_PASS` are "included adapters with offline contract coverage," **not** "live-verified integrations"; no fabricated evidence; partial-but-honest manifests are the correct state, not a gap.

## 7. The prior Principal's demonstrated review standard (please maintain this bar)

The prior Principal repeatedly caught real contract defects that had passed initial Sparring review. Maintaining that exacting standard is part of the seat. Concretely, it caught:
- a **closure-ordering** inversion (a SOW that closed the unit before the final release, contradicting the ruling's own numbered step sequence);
- a **false citation** (a SOW citing `verify_runtime_dependencies.py` as containing credential heuristics — it contains none);
- an **incoherent verifier contract** (a secret-scanner entropy rule that would reject the manifest's own required 40/64-char SHAs/digests);
- a **factual imprecision** ("atomic two-write transaction" for a three-write transaction);
- a **missing living-document deliverable** (a required `done_when` correction not actually required by the SOW).
The through-line of the bar: **trace every requirement's ordering and completeness against its governing authority, and every contract against the inputs it runs on** — not merely confirm each piece is individually present or cited.

## 8. Where to read the durable record

- `docs/rulings/index.md` and the ruling files it lists.
- `docs/sows/` — the SOWs, including `…-educational-control-plane.md` (the top-level design memo with `done_when`, `sequencing`, and the amendments).
- `docs/v1-unit*.md` — per-unit acceptance records (the authoritative "what each unit did / did not do").
- `docs/evidence/unit12/` — the Unit 12 proof-pack manifest and evidence files (partial-but-honest).
- GitHub PRs (roughly #22 → #49) — the full review/merge/correction trail; each Sparring review and Principal decision was filed there at an exact head.

## 9. How the new Principal picks up right now

1. Read this document, then the durable sources in §8 (repo wins on any conflict).
2. Resume the §3 envelope protocol for all messages.
3. Make the two open decisions in §5(a)/(b): accept PR #49 at `e58eae7…` (or require the M10 fix first). Sparring's APPROVED review and the M10 finding are filed on PR #49.
4. Thereafter, drive the Unit 12 terminal gates in §5(c) order, one separate authorization at a time, each bound to an exact commit.
5. Nothing beyond implementation acceptance is authorized yet: not the Andrea live session, credentialed execution, rc1/PyPI publication, either release tag, proof-pack acceptance, the status flip, or closure.

*End of Sparring-compiled handover. This document confers no authority; it exists so the incoming Principal starts fully informed. — Sparring (sovereign-agent).*
