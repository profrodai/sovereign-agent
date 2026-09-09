# Chapter 11 instructor guide — Tool isolation

**Created:** 2026-09-09 · **Status:** DRAFT / PEDAGOGY UNREVIEWED

## Objective and observable evidence

Build dispatch from registry lookup through allowlist, strict arguments, write guard and bounded JSON result. Refuse before invoking an unauthorized handler and keep raw validation inputs out of errors. Install the method in the real Dispatcher and observe handler invocation counters, not just returned text.

Unit A constructs the complete function in the actual runtime copy and saves its code, hashes and observed connection. Unit B consumes that code, injects the chapter failure, repairs the boundary and transfers to changed inputs. Do not replace these units with the legacy one-function answer worksheet.

## Facilitation

Allow 90–120 minutes for A and 75–90 for B; these are planning estimates, not measured classroom duration. Have learners predict before execution, compare in pairs, then use the three hints progressively. Reduce the starting scaffold for students already fluent in the relevant Python and SQL; retain the same behavioral obligations.

A known tool can still be unavailable to this particular worker. Ask what Lucy loses: Private shop data can leave a registered handler despite Lucy withholding permission to use it.

## Evidence and assessment

Run separate instructor solutions and runtime-transfer holdouts in a fresh local kernel. The starter must remain incomplete; an execution receipt must not label it learner mastery. The hidden probes contain independently authored expected outcomes, including a valid path that defeats refuse-everything repairs. Remove hidden probes and solutions from distributed learner bundles.

Use an unseen tool name, a valid allowed read, a denied registered read, a consequential call and oversized output. Treat malformed handoffs as invalid evidence. A missing handoff blocks B; never manufacture the learner's A implementation. The handoff hash binds bytes but does not prove correctness; rerun it.

Use the program's existing educator rubric, with 90/100 and every dimension at least 3/5 as the review threshold. No score has been assigned by this generator. Mark learning design UNREVIEWED until a human evaluates it.

## Classroom and cost record

Record anonymously: attendance; completion by stage; minutes to first connection; hint levels; misconceptions; successful hidden transfer; quality of the causal explanation; revisions needed. Record author minutes separately for preparation, generation, execution, verification, site projection and correction. Leave unobserved values unknown. Do not record student names or raw submissions containing private data in the repository.

## Limits

Dispatcher admission is not OS or network containment; container execution remains a separate chapter experiment. Trusted subprocess execution is not OS/network containment. Student code can inspect its checkout; instructor-held cases are assessment separation, not a security boundary against hostile filesystem access.
