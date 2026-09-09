# Chapter 15 instructor guide — Operating and restoring

**Created:** 2026-09-09 · **Status:** DRAFT / PEDAGOGY UNREVIEWED

## Objective and observable evidence

Construct restore from a separate compatible backup: verify integrity and schema, prepare a fresh epoch, clear old ownership, revoke approvals, pause, publish the authority marker and copy into the same database inode. Back up real queued work, restore and attempt a claim through the normal worker API before and after an explicit reconciliation/resume decision.

Unit A constructs the complete function in the actual runtime copy and saves its code, hashes and observed connection. Unit B consumes that code, injects the chapter failure, repairs the boundary and transfers to changed inputs. Do not replace these units with the legacy one-function answer worksheet.

## Facilitation

Allow 90–120 minutes for A and 75–90 for B; these are planning estimates, not measured classroom duration. Have learners predict before execution, compare in pairs, then use the three hints progressively. Reduce the starting scaffold for students already fluent in the relevant Python and SQL; retain the same behavioral obligations.

Pausing the old database is insufficient if the copied snapshot itself is unpaused. Ask what Lucy loses: Lucy’s restored snapshot starts work before later supplier activity and physical stock have been reconciled.

## Evidence and assessment

Run separate instructor solutions and runtime-transfer holdouts in a fresh local kernel. The starter must remain incomplete; an execution receipt must not label it learner mastery. The hidden probes contain independently authored expected outcomes, including a valid path that defeats refuse-everything repairs. Remove hidden probes and solutions from distributed learner bundles.

Retain backup hashes, repeat restore, compare authority epochs and test same-path or missing backups. A failed preflight must preserve live work. Treat malformed handoffs as invalid evidence. A missing handoff blocks B; never manufacture the learner's A implementation. The handoff hash binds bytes but does not prove correctness; rerun it.

Use the program's existing educator rubric, with 90/100 and every dimension at least 3/5 as the review threshold. No score has been assigned by this generator. Mark learning design UNREVIEWED until a human evaluates it.

## Classroom and cost record

Record anonymously: attendance; completion by stage; minutes to first connection; hint levels; misconceptions; successful hidden transfer; quality of the causal explanation; revisions needed. Record author minutes separately for preparation, generation, execution, verification, site projection and correction. Leave unobserved values unknown. Do not record student names or raw submissions containing private data in the repository.

## Limits

No host reboot or external supplier reconciliation is proved by this local exercise. Trusted subprocess execution is not OS/network containment. Student code can inspect its checkout; instructor-held cases are assessment separation, not a security boundary against hostile filesystem access.
