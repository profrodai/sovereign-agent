# Complete the nineteen-chapter construction

**Updated:** 2026-09-09 · **Status:** ACTIVE CONSTRUCTION PLAN

The current teaching collection has one nineteen-chapter map and four reader-facing assets: Teaching Book, Exercise Book, Solutions Book and Educator Guide. This plan records the work after reorganizing those assets. Sixteen manuscript drafts and their reference checkpoints have been retained. Chapters 4, 7 and 13 now expose the missing foundational lessons as clearly marked construction briefs. They are not yet completed chapters.

The quality benchmark is a self-contained professional technical textbook. “Manning level” describes teaching and editorial quality, not a publisher destination. No publisher submission belongs in this plan.

## The three chapter additions

| Chapter | Why it needs dedicated space | Reader-owned output | Consumed next |
| --- | --- | --- | --- |
| [4: Durable state](ch04/README.md) | Persistence and transaction foundations currently arrive through a supplied wrapper | Minimal store, explicit transactions, migrations, immutable event append | Memory in 5 and work in 7 |
| [7: Durable work](ch07/README.md) | Intake, completion and delivery have different failure states, crowded into messaging | Durable admission, basic claim, atomic terminal state/report creation | Telegram in 8 and scheduling in 9 |
| [13: MCP](ch13/README.md) | Protocol connection and OS containment are different concepts and environments | Bounded stdio initialization, discovery and allowed invocation | Isolation in 14 |

Each linked brief contains prerequisites, first-use concepts, a build/fail/repair sequence, interface requirements, exact ninety-minute Unit A and B plans and independently authored acceptance cases. The complete prose, examples, learner code and notebooks remain explicit deliverables. Chapter 14 currently retains its MCP teaching so restructuring does not discard content; that material moves and expands only when Chapter 13 is authored and tested.

## One chapter map across four assets

Stable lesson identity is separate from display number. This map preserves the meaning of previously distributed material while giving new readers one sequence.

| Current chapter | Topic | Previous sixteen-chapter number |
| --- | --- | --- |
| 1 | First model call | 1 |
| 2 | Typed shop tools and Pydantic | 2 |
| 3 | Owned model/tool loop | 3 |
| 4 | Durable SQLite state | New |
| 5 | Memory | 4 |
| 6 | Tested skills | 5 |
| 7 | Durable work and reports | New |
| 8 | Telegram | 6 |
| 9 | Schedules and stock events | 7 |
| 10 | Spending permissions | 8 |
| 11 | Ambiguous supplier outcomes | 9 |
| 12 | Worker recovery | 10 |
| 13 | MCP protocol | New standalone lesson |
| 14 | Isolation | 11 |
| 15 | Evaluation | 12 |
| 16 | Controlled improvement | 13 |
| 17 | Bounded delegation | 14 |
| 18 | Deployment and maintenance | 15 |
| 19 | Integrated day | 16 |

Older numbered releases retain their original meaning in historical records. Active manuscript links, checkpoint paths, companion numbers and classroom labels use the current map. Do not relabel an old binary archive and imply its contents were rebuilt.

## Telegram and operating integrations

Telegram is implemented in the reference runtime and taught in Chapter 8. The actual path is authenticated intake → durable work/cursor transaction → claim → context and loop → terminal work/report transaction → delivery disposition. The outbox is created by the reference schema's terminal-state triggers. A source trace establishes this wiring; fixture tests and live observations establish different behavior.

| Integration | Current teaching/reference evidence | Remaining construction or acceptance |
| --- | --- | --- |
| Telegram | Offline authenticated admission, duplicate/cursor behavior, work routing, report delivery and UNKNOWN handling | Connect the new learner inbox/outbox; complete a dedicated bot/handset exchange with sanitized identity/receipt evidence; handle structured retry delays in a bounded adapter |
| Schedules | Durable due slots and stock episodes enter the same work path; idle operation does not require a model | Consume Chapter 7's learner queue and demonstrate restart/coalescing; keep UTC interval scope explicit |
| Local skills | TOML versions, candidate evaluation, explicit activation and context selection | Introduce TOML/hashing before use and connect the cumulative learner store; skill text cannot grant tool authority |
| Permissions | Exact proposal, expiration/revocation and shared spend reservations | Break dense transactional methods into taught increments; independently test simultaneous reservation and stale consent |
| Supplier and receiving | Controlled independent ledger, lost-response reconciliation and receiving | Preserve UNKNOWN; reconcile physical stock, pending stock and actual expenditure separately |
| Worker recovery | Killed/stale-worker reference experiments and ownership generations | Extend the basic learner claim with tested takeover/fencing; never imply a local fence recalls a remotely accepted request |
| MCP | Bounded stdio reference client; optional pinned ZeoCore interoperability | Author Chapter 13 and connect learner validation/allowlist; keep ZeoCore optional and separate |
| Container isolation | Configured Linux/container reference observations | Separate protocol permissions from filesystem/network/process enforcement; repeat measured boundaries on the final supported setup |
| Evaluation and improvement | Independent outcomes, strong baseline, explanation blind spot, versioned activation and rollback | Preserve failures and fresh-case discipline; measure learner comprehension and operator effort; a green trace is not prose acceptance |
| Delegation | Bounded child task, deadline/cancellation and shared budget; plain-function comparison | Explain first-use subprocess and budget concepts; retain evidence that delegation earns its added complexity |
| Linux operation | Explicit service, backup/restore and compatible-code maintenance reference receipts | Prove final-release operation on the supported host and recover against independent post-snapshot effects |
| Integrated day | Real controlled supplier and worker processes with fixture model/Telegram | Execute through the complete learner package and retain independent results; add field evidence without reclassifying fixtures as live |

Telegram's core lesson remains account-free. A separate field exercise requires a dedicated account, test-message consent and actual handset inspection. Record source revision, local work/report identities, sanitized API disposition and observed message. Cover restart after intake, restart before sending, duplicate requests and an uncertain send without automatic repetition. A simulated rate-limit response can test retry timing without forcing a live account to hit a service limit.

The optional [ZeoCore appendix](appendices/zeocore-interop-v2.md) demonstrates one bounded protocol seam in a separate environment. It does not introduce a mandatory framework or promise a broad current integration catalog. No additional channel, marketplace, web gateway, general cron engine or autonomous real purchasing is needed to satisfy this edition's scope.

## Teaching and companion deliverables

The completed sequence requires **38 ninety-minute learner units**, two per chapter: **57 hours of dedicated core practice**. Unit A constructs and connects; Unit B diagnoses, repairs and transfers. Each unit requires a student notebook and matching Markdown, a separate worked solution notebook/Markdown, progressive hints, independently authored outcomes and a saved learner artifact. That means 38 student notebooks, 38 solution notebooks, 76 matching Markdown files and 19 educator chapter guides.

The existing sixteen-chapter course contributes 32 learner units and their worked counterparts. Their numerical migration is not proof that the new cumulative handoffs are built. All existing units must be reviewed against the new prerequisites and learner ownership; the three additional chapters add six new learner units plus six worked counterparts.

Each unit begins with observable goals and a prerequisite check. A new library or concept needs its smallest example, predicted output, explanation, deliberate failure, repair and eventual integration. Include retrieval questions and a changed-constraint task. Published additional cases become development material once they inform a repair; do not describe them as unseen tests forever.

Add three optional ninety-minute field worksheets for real Telegram, configured containment and Linux lifecycle/maintenance. These sit in the educator field material with explicit learner instructions and evidence forms, separate from the 38 core units. Completing all three gives 61.5 planned practice hours. Unavailable credentials or host features must not strand the core course, while simulated alternatives must not certify real field acceptance.

Plan approximately **100,000–115,000 main-manuscript prose words** to provide slower construction and explanation. The pre-expansion measurement was 65,401 words outside code fences. This is an allocation guide, not a padding requirement or a page-count promise. Typeset SQLite, Telegram and ambiguous-order samples before deriving a print extent. Human reader trials determine whether the material teaches well.

## Implementation sequence and acceptance

| Order | Work | Required exit observation |
| --- | --- | --- |
| 1 | Establish four assets and nineteen-chapter identities | One visible map; preserved source content; active links and executable reference checks pass |
| 2 | Finalize cumulative learner ownership and interface contracts | Each chapter names owned code, previous definitions, infrastructure and fixtures |
| 3 | Author SQLite and its two units | Empty-root build works; rollback, conflicts and future-schema refusal fail correctly |
| 4 | Author durable work and refocus Telegram/schedules | Both producers invoke the learner's actual admission/finish/outbox implementation |
| 5 | Author MCP and refocus isolation | Independent protocol and host evidence; no unauthorized advertised tool invocation |
| 6 | Expand dense existing chapters and all companion handoffs | 38 learner/38 worked units execute independently with matching Markdown and guides |
| 7 | Run final learner day and field observations | Independent supplier reconciliation plus separately labeled phone/container/Linux evidence |
| 8 | Synchronize site/downloads and review the rendered assets | Exact source pins, unambiguous four-asset navigation, readable code/layout and recorded learner timing |

The previously inspected site repository projection predates the latest Pydantic and evaluation improvements. Site synchronization must consume the current source and new hierarchy together, with a separately recorded deployed source pin. A merged source PR or a valid GitHub link does not establish what the website currently serves.

Completion works backward from the title: a Python-capable reader constructs the essential system, receives an authenticated phone request, retains appropriate memory, wakes without idle model calls, respects permissions, recovers from process and external-effect uncertainty and produces a report supported by independent records. See [OWNERSHIP.md](OWNERSHIP.md) for the empty-workspace and deliberately broken-function checks. Reader comprehension, classroom pacing and print readability still require observed human review.
