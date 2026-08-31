# SOW: Sovereign Agent 1.0 — executable textbook

```yaml
sow: sovereign-agent-v1-educational-control-plane
project: sovereign-agent
stream: v1-educational-reboot
status: DESIGN
lifecycle: DESIGN-MEMO
created: 2026-08-25
updated: 2026-08-25
sequencing: unit-5-manual-slice; unit-9-first-pulse; unit-10-ch0-7; unit-11-ch8-12
work_repo: https://github.com/zeroemployeeorg/sovereign-agent
sow_repo: TBD
done_when: >-
  python -m pytest -q -> 0 failures;
  python scripts/verify_curriculum.py -> exit 0;
  python scripts/verify_runtime_dependencies.py -> exactly pydantic;
  sovereign-agent demo store --mode simulated -> outcome ACCEPTED;
  foreground and installed-supervisor pulse tests -> proactive governed work with durable receipts;
  timed Andrea-profile quickstart -> first accepted outcome within 10 minutes;
  30-day Sovereign Store pilot -> redacted proof pack accepted
```

This work repository records SOW metadata and the binding ruling so
implementation history and authorization agree. The full design memo lives with
the originating stream; holdings that change the package boundary are in
[ruling 2026-08-25 educational reset](../rulings/2026-08-25-educational-reset.md).

**Correction (2026-08-31), additive — original text below unedited:** the
`done_when` clause's line above,
"30-day Sovereign Store pilot -> redacted proof pack accepted", and
sequencing amendment 6 below's own clause "then starts the 30-day pilot.
Unit 12 finishes the pilot..." are both **superseded**, per
`docs/rulings/2026-08-30-unit11-local-closure-supersedes-real-deployment-gate.md`
(Unit 11 closes on the local, learner-controlled pilot-start mechanism; no
real 30-day deployment pilot is assumed or required) and per
`docs/rulings/2026-08-31-unit12-scope.md`'s own Holding 1, whose exact
replacement text for the superseded `done_when` line is:

> local, learner-controlled Sovereign Store release evaluation -> redacted Unit 12 proof pack accepted

This replaces only the meaning of "30-day Sovereign Store pilot -> redacted
proof pack accepted" in the `done_when` clause above and of "then starts the
30-day pilot. Unit 12 finishes the pilot..." in sequencing amendment 6
below; the original clauses remain unedited at their own citations, exactly
as this project's own established discipline requires for every prior
superseded-but-preserved passage. No real 30-day deployment pilot, real
pilot-start act, or governance receipt is claimed by, or required for, this
project's own completion.

## Decision in one sentence

Rebuild sovereign-agent as the most didactic possible Python library for
learning how a Zero-Employee Organization turns an outcome into governed work
performed by actors whose intelligence comes from Claude Code, Codex, or
Cursor—and make Zero Employee the obvious graduation path when the learner is
ready for production.

## Open questions

| id | claim | status | resolution |
| --- | --- | --- | --- |
| OQ-1 | Confirm that Sovereign Agent 1.x may intentionally break the v0.7 public API and reposition the package as an executable textbook. | RESOLVED | Principal approval, 2026-08-25. |
| OQ-2 | Confirm whether the canonical short executable remains `sovereign-agent` or additionally gains the `sov` alias. | RESOLVED | Retain only `sovereign-agent` for 1.0. No `sov` alias. |
| OQ-3 | Confirm the canonical user-facing name for the opt-in resident process: supervisor, resident supervisor, or organization service. | RESOLVED | Teach **supervisor** as the control loop. Use **service** only for `install` / `status` / `uninstall`. One supervisor; service is hosting. |

## Sequencing amendments (2026-08-25)

1. Introduce the Sovereign Store **walking skeleton** during Units 2–5
   (`Product`, `InventoryPosition`, `CashEntry`, transactional mutations,
   scripted sale, inventory signal, replenishment SOW). Unit 11 expands that
   skeleton; it does not create the store from nothing.
2. Develop the curriculum **alongside** implementation units. Checkpoint tags
   name **commits**, not branches. Preserve those tagged commits in the
   eventual `main` ancestry. Do not maintain chapter-specific branches.
3. Persistence wording: JSON/TOML is canonical for committed governance;
   SQLite is canonical for operational state; Markdown is generated.
4. **Unit 5 is not proactive.** Pulse does not exist yet. The Unit 5 offline
   slice is: sale → inventory signal persisted → manually dispatched
   replenishment SOW → Scripted Operator → evidence → Sparring → acceptance.
5. **Unit 9 is the first fully proactive milestone:** sale → inventory signal
   → deterministic wake gate → pulse → replenishment work created without a
   human prompt → Scripted Operator → evidence → Sparring → acceptance.
6. **Curriculum completion is staged.** Unit 10 completes and verifies
   Chapters 0–7 and establishes instructor-note and drift-verification
   machinery. It does not claim Chapters 8–12 exist. Unit 11 expands the
   Store and lands Chapters 8–12 alongside those features, then starts the
   30-day pilot. Unit 12 finishes the pilot, completes all curriculum
   verification, conducts Andrea-profile soaks, runs provider smokes, and
   releases.
7. Unit 1 may add the Chapter 0 directory and narrative shell.
   `book-v1-ch00` is tagged only when the scripted first-success experience
   actually works (expected: Unit 5).

## Related documents

- [Educational reset ruling](../rulings/2026-08-25-educational-reset.md)
- [Migration v0.7 to v1](../migration-v0.7-to-v1.md)
- [v0.7 maintenance](../v0.7-maintenance.md)
- [v1 removal manifest](../v1-removal-manifest.md)
- [Unit 9 SOW: Pulse and proactive governed work](sovereign-agent-v1-unit9-pulse-proactive-work.md)
- [Unit 10 SOW: curriculum completion, Chapters 0-7](sovereign-agent-v1-unit10-curriculum-completion.md)
- [Unit 11 SOW: Store expansion, Chapters 8-12, pilot-start mechanism](sovereign-agent-v1-unit11-store-expansion-pilot-start.md)
- [Unit 12 SOW: release evaluation, proof pack, Andrea protocol, 1.0.0 release](sovereign-agent-v1-unit12-release-evaluation.md)
