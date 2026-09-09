# What you construct and what is supplied

**Updated:** 2026-09-09 · **Status:** DRAFT

The teaching target is one cumulative learner-owned agent. The current draft contains a mixture of code constructed in the chapters and supplied reference infrastructure. A checkpoint importing a finished helper demonstrates that helper's behavior; it does not establish that the reader built the helper.

## The current executable boundary

Chapter 1 is a direct model-request example with an offline response fixture. Chapter 2 constructs tool arguments, handlers and dispatch in `learner/ch02.py`, reusing Chapter 1's shop data. Chapter 3 constructs the model/tool loop and parsing in `learner/ch03.py`. Its HTTP path imports the supplied bounded transport from `sovereign_agent.http_transport`. The saved learner files are completed comparison implementations; use your own checkout to construct and change them.

Later chapters print substantial implementation logic, while their executable reference checkpoints also import supplied runtime and controlled-shop components. The table lists direct imports in checkpoint source, not an exhaustive transitive dependency graph. A checkpoint with no direct import can still load another checkpoint or learner file that imports one.

| Chapter | Stable lesson identity | Direct supplied runtime imports in checkpoint |
| --- | --- | --- |
| 1 | first-model-call | No direct finished-runtime import; see transitive dependencies below |
| 2 | shop-tools | `sovereign_agent.model_turn`, `sovereign_agent.tool_dispatch` |
| 3 | agent-loop | No direct finished-runtime import; see transitive dependencies below |
| 4 | durable-state | PLANNED: learner construction and handoff not yet implemented |
| 5 | memory | `reference_organizations.store.agent`, `sovereign_agent.agent_loop`, `sovereign_agent.assistant_context`, `sovereign_agent.assistant_work`, `sovereign_agent.database`, `sovereign_agent.model_turn` |
| 6 | skills | `reference_organizations.store.agent`, `reference_organizations.store.evaluation`, `sovereign_agent.agent_loop`, `sovereign_agent.assistant_context`, `sovereign_agent.database`, `sovereign_agent.model_turn` |
| 7 | durable-work | PLANNED: learner construction and handoff not yet implemented |
| 8 | messaging | `reference_organizations.store.agent`, `reference_organizations.store.evaluation`, `sovereign_agent.agent_loop`, `sovereign_agent.assistant_context`, `sovereign_agent.assistant_work`, `sovereign_agent.database`, `sovereign_agent.model_turn`, `sovereign_agent.telegram_channel` |
| 9 | scheduling | `reference_organizations.store.agent`, `reference_organizations.store.assistant`, `reference_organizations.store.stock_conditions`, `sovereign_agent.assistant_work`, `sovereign_agent.database`, `sovereign_agent.model_turn` |
| 10 | approval | `reference_organizations.store.agent`, `reference_organizations.store.supplier`, `sovereign_agent.assistant_orders`, `sovereign_agent.assistant_work`, `sovereign_agent.database` |
| 11 | ambiguous-order | `reference_organizations.store.agent`, `reference_organizations.store.supplier`, `sovereign_agent.assistant_orders`, `sovereign_agent.assistant_work`, `sovereign_agent.database` |
| 12 | worker-recovery | `reference_organizations.store.agent`, `reference_organizations.store.assistant`, `reference_organizations.store.supplier`, `sovereign_agent.assistant_orders`, `sovereign_agent.assistant_work`, `sovereign_agent.database` |
| 13 | mcp | PLANNED: learner construction and handoff not yet implemented |
| 14 | isolation | `reference_organizations.store.agent`, `reference_organizations.store.assistant`, `reference_organizations.store.extra_tools`, `sovereign_agent.assistant_work`, `sovereign_agent.database`, `sovereign_agent.model_turn`, `sovereign_agent.sandbox_tool`, `sovereign_agent.tool_dispatch` |
| 15 | evaluation | `reference_organizations.store.agent`, `reference_organizations.store.evaluation`, `reference_organizations.store.improvement`, `sovereign_agent.assistant_context`, `sovereign_agent.model_turn` |
| 16 | improvement | `reference_organizations.store.agent`, `reference_organizations.store.improvement`, `sovereign_agent.assistant_context`, `sovereign_agent.database`, `sovereign_agent.events`, `sovereign_agent.model_turn` |
| 17 | delegation | `reference_organizations.store.agent`, `reference_organizations.store.assistant`, `reference_organizations.store.delegation`, `sovereign_agent.assistant_work`, `sovereign_agent.database` |
| 18 | operation | `reference_organizations.store.account_recovery`, `reference_organizations.store.agent`, `reference_organizations.store.assistant`, `sovereign_agent`, `sovereign_agent.assistant_service`, `sovereign_agent.database`, `sovereign_agent.model_turn` |
| 19 | acceptance | `reference_organizations.store.agent`, `reference_organizations.store.assistant`, `reference_organizations.store.delegation`, `reference_organizations.store.operating_report`, `reference_organizations.store.stock_conditions`, `reference_organizations.store.supplier`, `sovereign_agent`, `sovereign_agent.agent_loop`, `sovereign_agent.database`, `sovereign_agent.telegram_channel` |

## The intended cumulative construction contract

Every authored chapter must name four categories before the first implementation: definitions consumed from previous learner work, definitions constructed here, standard/third-party infrastructure, and supplied test-only fixtures. A field or helper not introduced earlier must be explained when first used.

The new Chapter 4 builds the store and transaction boundary. Chapter 5 adds memory tables and context selection; Chapter 6 adds versioned skill selection. Chapter 7 builds admission, basic work state and atomic terminal reports. Chapters 8 and 9 become adapters into that same queue. Chapter 12 adds ownership generations and recovery. Chapter 13 builds the bounded MCP connection before Chapter 14 applies separate OS containment.

The finished `sovereign_agent` and `reference_organizations` packages remain comparison and fixture material. They may not silently execute essential learner behavior in the cumulative acceptance. Existing reference demonstrations remain available while that migration is authored; they must keep their supplied-code label until the corresponding learner handoff is proved.

## Proof that the learner implementation is connected

Start with an empty learner workspace and the declared environment. Follow the printed save/import instructions, then trace an authenticated request through learner admission, context, loop, tools, state, completion and report delivery. The test must observe actual input reaching the learner's function and persisted results leaving it.

For each chapter, deliberately remove or corrupt one essential learner function. An independent behavior check must fail. A test whose expected answer comes from the same function, or whose finished reference runtime silently takes over, cannot prove construction. Keep fixtures and observer queries separate from expected-result generation.

The final day must reconcile the learner's result against the independent controlled supplier ledger. Live Telegram, container and Linux observations have additional explicit facilities and evidence; portable fixture success is recorded separately. See [the construction roadmap](EXPANSION.md) for remaining deliverables and release conditions.
