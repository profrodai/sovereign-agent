# Chapter 10 instructor guide — Worker recovery

**Created:** 2026-09-09 · **Status:** DRAFT / PEDAGOGY UNREVIEWED

## Objective and observable evidence

Reconstruct the full worker assertion: verify paused state and external authority marker, compare database and claim epochs, match the full running lease identity and enforce delegation deadline and parent cancellation. Call observe through the real write path, then replace the epoch while keeping the same database and process.

Unit A constructs the complete function in the actual runtime copy and saves its code, hashes and observed connection. Unit B consumes that code, injects the chapter failure, repairs the boundary and transfers to changed inputs. Do not replace these units with the legacy one-function answer worksheet.

## Facilitation

Allow 90–120 minutes for A and 75–90 for B; these are planning estimates, not measured classroom duration. Have learners predict before execution, compare in pairs, then use the three hints progressively. Reduce the starting scaffold for students already fluent in the relevant Python and SQL; retain the same behavioral obligations.

A matching worker name and lease generation cannot rescue an old restore epoch. Ask what Lucy loses: A worker from an earlier authority epoch can append evidence to Lucy’s current work.

## Evidence and assessment

Run separate instructor solutions and runtime-transfer holdouts in a fresh local kernel. The starter must remain incomplete; an execution receipt must not label it learner mastery. The hidden probes contain independently authored expected outcomes, including a valid path that defeats refuse-everything repairs. Remove hidden probes and solutions from distributed learner bundles.

Keep a fresh claimant writable while refusing stale epoch, expired lease, missing marker and changed role. Count transcript rows after every attempt. Treat malformed handoffs as invalid evidence. A missing handoff blocks B; never manufacture the learner's A implementation. The handoff hash binds bytes but does not prove correctness; rerun it.

Use the program's existing educator rubric, with 90/100 and every dimension at least 3/5 as the review threshold. No score has been assigned by this generator. Mark learning design UNREVIEWED until a human evaluates it.

## Classroom and cost record

Record anonymously: attendance; completion by stage; minutes to first connection; hint levels; misconceptions; successful hidden transfer; quality of the causal explanation; revisions needed. Record author minutes separately for preparation, generation, execution, verification, site projection and correction. Leave unobserved values unknown. Do not record student names or raw submissions containing private data in the repository.

## Limits

This local fence cannot recall an external request already admitted before replacement. Trusted subprocess execution is not OS/network containment. Student code can inspect its checkout; instructor-held cases are assessment separation, not a security boundary against hostile filesystem access.
