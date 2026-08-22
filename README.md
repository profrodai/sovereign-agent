# sovereign-agent

**The eight architectural decisions every serious agent system converges on — implemented as a library you can use, and a tutorial you can read.**

Debug by `cat`. Crash-recover by `ls`. Teach by reading the same code that runs in production.

<p align="center">
  <a href="https://github.com/zeroemployeeorg/sovereign-agent/actions/workflows/ci.yml"><img alt="CI status" src="https://github.com/zeroemployeeorg/sovereign-agent/actions/workflows/ci.yml/badge.svg"></a>
  <a href="https://pypi.org/project/sovereign-agent/"><img alt="PyPI version" src="https://img.shields.io/pypi/v/sovereign-agent.svg"></a>
  <a href="https://pypi.org/project/sovereign-agent/"><img alt="Python versions" src="https://img.shields.io/pypi/pyversions/sovereign-agent.svg"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/pypi/l/sovereign-agent.svg"></a>
  <a href="https://github.com/zeroemployeeorg/sovereign-agent/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/zeroemployeeorg/sovereign-agent.svg?style=social"></a>
</p>

> **Repository identity.** The canonical home is
> [`zeroemployeeorg/sovereign-agent`](https://github.com/zeroemployeeorg/sovereign-agent).
> Older `sovereignagents/...` URLs still resolve by GitHub redirect but are not
> canonical; new links should use `zeroemployeeorg`.

```bash
pip install sovereign-agent
```

```python
from sovereign_agent import run_task, register_tool

@register_tool
def get_weather(city: str) -> dict:
    """Look up current weather for a city."""
    return {"city": city, "temperature": 18, "condition": "rainy"}

result = run_task("What's the weather in Edinburgh?")
print(result.summary)
# → "Weather in Edinburgh: 18°C, rainy."
```

The agent ran a planner, called `get_weather`, wrote a trace, and saved every artifact to `sessions/sess_<id>/`. Inspect it with `ls -R sessions/sess_<id>`. That's not a metaphor — it's how you debug this system.

---

## What sovereign-agent is, exactly

Two things in one repository:

**A production library** you `pip install` and use to build agents.
**A build-from-scratch curriculum** that reconstructs the library in five chapters with tests, so you learn by implementing.

The chapters rebuild the v0.2 substrate and re-export the production primitives
they teach. A CI check (`tools/verify_chapter_drift.py`) prevents those mapped
primitives from drifting. v0.3 features are taught in numbered unit documents;
the chapters intentionally do not claim whole-package parity. See the
[teaching-surface decision](docs/teaching-surface.md).

sovereign-agent is **not** trying to be the next Claude Code or OpenHands. It's the thing you read to understand *why* they and every other production agent system converged on the same eight architectural decisions.

---

## The eight decisions (this is the product)

Every production agent system I've read the internals of — Claude Code, OpenHands, Aider, SWE-agent, Devin, Cognition's public work — has independently arrived at the same eight decisions. sovereign-agent is those decisions, made explicit, with code you can run.

1. **Sessions are directories.** `sessions/sess_<12hex>/` contains everything — memory, IPC, state, logs, artifacts. No database. No shared tables.
2. **State is forward-only.** A session never transitions backwards. Retries are new sessions, linked to the old one.
3. **Tickets for every operation.** Append-only audit trail. Tickets are to your agent what commits are to a git repo.
4. **Manifests verify by SHA-256.** Detect accidental edits, disk corruption, and tampering. Not cryptographic security — this is about catching the mistakes you actually make.
5. **Atomic rename for IPC.** Two halves of the agent communicate by writing files. No brokers, no Kafka, no Redis. POSIX's `rename()` is the only IPC primitive you need until proven otherwise.
6. **Lock at the session level.** Not finer (deadlocks), not coarser (unscalable). One serialization boundary per session gives you multi-file consistency for free.
7. **Parse JSON defensively.** The LLM is lying. Write a parser that handles what the model *actually* produces, not what the prompt *instructed* it to produce.
8. **Register tools explicitly.** Prompts are advisory; the registry is physics. When the model persistently reaches for a tool you don't want used, remove the tool — don't write the third negative instruction.

Each decision *removes* a class of bugs rather than handling them. That's why the decisions age well.

Full walk-through in [`docs/architecture.md`](docs/architecture.md). Note that
the architecture doc enumerates the same system from an implementation angle and
so numbers its decisions differently; the two lists overlap but are not a 1:1
mapping, and neither is a renumbering of the other.

---

## The ninth thing nobody converges on, but should: dataflow integrity

The framework can guarantee that tools were called, tickets were written, manifests verified, state advanced. **That is necessary but not sufficient.** You also need to verify the LLM *used* its tool outputs.

Every scenario in this repo ships with a dataflow integrity audit. The research-assistant scenario checks that every arXiv ID cited in the report was actually returned by `web_lookup` — not fabricated from training data. The code-reviewer scenario checks that the review references findings the analyzer actually returned.

This is not a hypothetical concern:

> *One morning I had a framework with 148 passing tests and three clean scenarios. I ran the code reviewer against a real LLM for the first time. It produced a perfectly-formatted review of code that did not exist — named `add`, `multiply`, `divide`. The framework reported ✓ success, ✓ manifest, ✓ complete. Every structural guarantee held. The output was pure fiction.*

(148 was the test count at v0.1.0; see [Status](#status) for the current number.)

"It ran" is not "it worked." The library gives you the first; your scenario has to verify the second. Every example in this repo demonstrates the pattern.

---

## Install

```bash
pip install sovereign-agent              # core
pip install "sovereign-agent[all]"       # + optional extras (voice, observability)
```

Development tooling lives in the PEP 735 `dev` dependency *group*, not an extra —
so it is `uv sync --group dev` (or `pip install -e . --group dev`), not
`pip install "sovereign-agent[dev]"`.

Requires Python 3.12+.

**Docker is not available.** There is a `docker` extra, but it only installs the
Docker SDK; `DockerWorker` is a stub that raises `NotImplementedError` on
`run_session()`. The supported isolated backend is `worker_backend='subprocess'`
(Landlock on Linux ≥ 5.13, `sandbox-exec` on macOS). See
[v0.3 non-goals](docs/v0.3-non-goals.md).

---

## The two halves

The decision-8 principle — *prompts are advisory, registries are physics* — generalizes. Not every constraint is a tool registry. Some constraints are rules. sovereign-agent ships a **loop half** (ReAct-style LLM reasoning) and a **structured half** (deterministic Python) that communicate by atomic-rename IPC.

```python
from sovereign_agent import LoopHalf, StructuredHalf, Rule

loop = LoopHalf(planner=planner, executor=executor)

structured = StructuredHalf(rules=[
    Rule(name="commit_under_cap",
         condition=lambda d: d["deposit"] <= 300,
         action=commit_booking),
    Rule(name="escalate_over_cap",
         condition=lambda d: d["deposit"] > 300,
         escalate_if=lambda d: True),
])
```

The loop decides what to try. The structured half decides what's allowed. No amount of prompt engineering can bypass a rule — the business constraint lives in Python where it belongs.

This isn't new. It's how every financial, regulatory, or high-stakes agent system eventually ends up structured. The name varies ("policy layer," "guardrails," "rules engine") but the pattern is the same. sovereign-agent makes it the default.

---

## What shipped in v0.2.0 (the published release)

Five capabilities that came out of running sovereign-agent against real LLMs and hitting real failures:

**Parallel tool dispatch.** Tools marked `parallel_safe=True` run concurrently. Writes and handoffs serialize automatically. Five 0.3s calls finish in 0.31s instead of 1.5s.

**Worker isolation without Docker.** Linux ≥5.13 gets kernel-level Landlock. macOS gets `sandbox-exec`. No container runtime needed. Tool compromise can't escape the session directory.

**Session resume.** Resume any terminal session as a new child. Parent context auto-prepends to the child's `SESSION.md`. Chains preserve ancestry. Forward-only state is preserved — resumes are new sessions, never edits of the old.

**Verifier protocol.** Rule conditions accept callables, scikit-learn classifiers, or LLM judges. Same audit trail, different backend. Decision 6 generalized.

**Human-in-the-loop approval.** Tools return `requires_human_approval=True`. The executor exits cleanly, writes the request to disk, and resumes when a human decides — seconds, hours, or days later. Nothing in memory.

Each is ~200-400 lines of code with tests. See `examples/` for end-to-end scenarios that use each one.

---

## What shipped in v0.3.0

The v0.3 package adds:

- **Channel adapters** — `ChannelAdapter` protocol plus a CLI adapter and an
  inbound router. Only `CHANNEL_REGISTRY` is exported in `__all__`; the adapter
  types are importable but not yet part of the semver surface.
- **Plugin registries** — a generic `Plugin` protocol and `Registry[T]`.
- **Worker backend integration** — orchestrator dispatch routes through
  `WorkerBackend` via `make_worker_backend()`.
- **Native CLI providers** — Codex CLI and Claude Code are probed, capability
  gated, parsed into normalized events, and executed through `WorkerBackend`
  without Sandcastle.
- **Liveness monitor** — stalled-session detection and heartbeat
  (`LivenessMonitor`, importable but not in `__all__`).

These additions are part of the v0.3 public contract where listed in
`sovereign_agent.__all__`. See
[`docs/v0.3-non-goals.md`](docs/v0.3-non-goals.md) for what v0.3 will *not* do,
and [`docs/branch-consolidation-2026-08-22.md`](docs/branch-consolidation-2026-08-22.md)
for how these branches landed.

---

## The architecture in one picture

```
   ┌─────────────────────────────────────────────────────────────┐
   │   LOOP HALF         Planner → Executor → Tools              │
   │   (reasoning)       ReAct-style, free-form LLM              │
   │                                                             │
   │        ▼ handoff via ipc/handoff_to_structured.json         │
   │                                                             │
   │   STRUCTURED HALF   Deterministic rules, classifiers,       │
   │   (constraints)     LLM judges — whatever you configure.    │
   │                     Binds what's allowed.                   │
   └─────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
   ┌─────────────────────────────────────────────────────────────┐
   │   sessions/sess_a382a2149fc1/                               │
   │   ├── session.json       # state machine, forward-only      │
   │   ├── SESSION.md         # the system prompt                │
   │   ├── workspace/         # tool outputs, agent artifacts    │
   │   ├── memory/            # persistent facts across runs     │
   │   ├── ipc/               # atomic-rename message passing    │
   │   ├── tickets/           # every operation recorded         │
   │   └── logs/trace.jsonl   # every event, every tool call     │
   └─────────────────────────────────────────────────────────────┘
```

---

## Debugging by `cat`

This is the visceral version of "sessions are directories." Last week I debugged five separate failures across three scenarios. Every one was diagnosed from three lines of JSONL:

```bash
$ cat sessions/sess_5ab10359c72a/logs/trace.jsonl
{"event_type": "executor.tool_called", "payload":
 {"tool": "read_file", "arguments": {"path": "workspace/source.py"},
  "success": false, "summary": "file not found"}}
{"event_type": "executor.tool_called", "payload":
 {"tool": "list_files", "arguments": {"path": "workspace"},
  "success": true, "summary": "0 entries"}}
{"event_type": "executor.tool_called", "payload":
 {"tool": "complete_task", "arguments":
  {"result": {"status": "failed",
              "reason": "No source file found in workspace"}}}}
```

The LLM never tried the analyzer tool. It looked for files that weren't there, gave up, marked the session complete. Three lines and I knew the fix (decision 8: remove the directory-listing tool from the registry; the model reaches for it reflexively).

No SELECT queries. No vendor viewer. No SDK. `cat`.

---

## Three surfaces, one codebase

```
sovereign-agent/
├── src/sovereign_agent/  # the library you pip install (src layout)
├── chapters/             # 5 tutorial chapters (minitorch-style, fill in the TODOs)
├── examples/             # 8 reference scenarios (research, code review, HITL, etc.)
├── docs/                 # architecture, API stability, deployment
└── tests/                # 500 collected tests — library + chapters + examples
```

- **If you want to ship an agent today** → read `src/sovereign_agent/` and pick scenarios from `examples/`
- **If you want to understand how it works** → read the chapters. Each one rebuilds a piece of the library. Your tests pass when you're done.
- **If you want the architecture argument** → [`docs/architecture.md`](docs/architecture.md)

The chapter/library drift check (`tools/verify_chapter_drift.py`) runs in CI for
the v0.2 primitives those chapters teach. The explicit v0.3 teaching scope is
documented in [`docs/teaching-surface.md`](docs/teaching-surface.md).

---

## Lineage

sovereign-agent stands on three lineages:

**Teaching artifacts with real libraries** — the pattern:
- [`fastai`](https://github.com/fastai/fastai) (Jeremy Howard) — the library + course pattern. sovereign-agent's biggest debt.
- [`minitorch`](https://github.com/minitorch/minitorch) (Sasha Rush) — rebuild-the-framework pedagogy. Chapters work like this.
- [`LLMs-from-scratch`](https://github.com/rasbt/LLMs-from-scratch) (Sebastian Raschka) — book + code as the same artifact. Reading order matters.
- [`nanoGPT`](https://github.com/karpathy/nanoGPT) (Andrej Karpathy) — small, readable, no magic.

**Production agent systems that converged on the same architecture**:
- [NanoClaw](https://github.com/qwibitai/nanoclaw) (Gavriel Cohen) — TypeScript reference implementation. Read `src/group-queue.ts`; two hours of reading and you'll see where sovereign-agent's patterns come from.
- [Claude Code](https://www.anthropic.com/news/claude-code) — session-as-directory, sub-agent isolation.
- [OpenHands](https://github.com/All-Hands-AI/OpenHands) — closest OSS cousin architecturally.
- [Aider](https://github.com/paul-gauthier/aider) — per-repo state in `.aider/`, same pattern simpler scope.
- [SWE-agent](https://arxiv.org/abs/2405.15793), [Devin](https://www.cognition.ai/blog) — per-task sandboxes.

**Papers that shaped the module design**:
- [ReAct](https://arxiv.org/abs/2210.03629) — the executor loop.
- [Reflexion](https://arxiv.org/abs/2303.11366) — memory patterns.
- [MemGPT](https://arxiv.org/abs/2310.08560) — hierarchical memory.
- [Voyager](https://arxiv.org/abs/2305.16291) — procedural memory; file-based skills.
- [SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering](https://arxiv.org/abs/2405.15793) — "give the agent a typewriter, not a console."

See [`CREDITS.md`](CREDITS.md) for the full list.

---

## Quick-start with a real LLM

```bash
# Configure your LLM endpoint (Nebius, OpenAI, or any OpenAI-compatible provider)
cp .env.example .env
# edit: set NEBIUS_KEY=sk-... and optionally swap models

# Verify everything is wired up — Python, uv, .env, models, imports, CI
make doctor

# Run a real scenario end-to-end
make example-research-real
```

A real-LLM run prints every step, every tool call, and finishes with a dataflow integrity audit. Illustrative shape of `example-research-real` output (model names and byte counts depend on your `.env` and the run):

```
▶ research-assistant  (real LLM)
  planner:  MiniMaxAI/MiniMax-M2.5
  executor: Qwen/Qwen3-235B-A22B-Instruct-2507
  ✓ plan produced: 1 subgoal, loop half
  ✓ web_lookup("retrieval augmented generation") → 2 results
  ✓ write_file(report.md) — 287 bytes
  ✓ complete_task

=== Dataflow integrity audit ===
  web_lookup calls: 1, successful hits: 2, unique papers returned: 2
  ✓ all 2 arXiv ID(s) came from web_lookup
  titles from web_lookup referenced in report: 2/2
```

If the model fabricates a paper the audit catches it and flags ✗ with the fabricated ID. This pattern is what you want to copy into your own scenarios.

---

## Launch-checklist-as-Makefile

The Makefile is also the documentation for the release workflow:

```
make doctor           # tabular status — Python, uv, .env, deps, imports, CI
make preflight        # lint + drift + pytest collection + demo importability
make test             # full suite (500 collected: 497 pass, 3 opt-in/platform skips)
make ci-real-estimate # cost preview for a full ci-real run (no API calls)
make ci-real          # run every -real scenario against a live LLM
make pre-publish      # audit for secrets, PII, forbidden files before public push
make ready-to-ship    # deterministic CI + audit + wheel/sdist clean-install proof
```

`make help` groups every target by category. `make doctor` output is tabular; paste it into an issue and a maintainer has full diagnostic context.

---

## Where things live

sovereign-agent is a well-behaved Python library. It never writes to your CWD when you `import sovereign_agent`. Different entry points write to different places by design:

| Entry point | Artifacts go to | Why |
|---|---|---|
| `sovereign-agent run <task>` (production) | `./sessions/` (your CWD) | Your deployment, your call |
| `python -m chapters.<n>.demo` | `$XDG_DATA_HOME/sovereign-agent/demos/` | Persists for inspection; outside your git tree |
| `python -m examples.<n>.run` (offline) | tempdir, auto-cleans | Deterministic dev runs |
| `python -m examples.<n>.run --real` | `$XDG_DATA_HOME/sovereign-agent/examples/` | Real-LLM runs burn tokens; keep artifacts |

Override via `SOVEREIGN_AGENT_DATA_DIR=<path>`.

---

## Status

**v0.4.0.** The package still exports **152** symbols in
`sovereign_agent.__all__` (the v0.3 surface, preserved). v0.4 adds a
governed-connectivity service as importable subpackages. See
[`docs/API.md`](docs/API.md) and [`docs/v0.4-operator-guide.md`](docs/v0.4-operator-guide.md).

- ✅ Framework: sessions, tickets, IPC, parallelism, isolation, resume, verifiers, HITL
- ✅ 522 tests collected — 519 pass, 3 opt-in/platform skips
- ✅ 8 reference scenarios, all with dataflow integrity checks
- ✅ 5 tutorial chapters, drift-checked against production code in CI
- 🚧 Voice pipeline, observability backends (Evidently/OTel) — skeletons, not implementations
- ✅ Channels, native Codex/Claude CLI providers, plugin registries, worker lifecycle, governed repository execution, durable seat registry and relay
- ❌ Docker worker backend — stub only; `DockerWorker.run_session()` raises `NotImplementedError`
- ❌ Vector-DB memory backends — not started, and a [v0.3 non-goal](docs/v0.3-non-goals.md)

Nothing in this repository is load-bearing for a production deployment you have
not read end to end yourself. The alpha label is not modesty.

---

## What sovereign-agent is not

It's not trying to replace Claude Code for daily coding or LangGraph for orchestration-heavy workflows. It's not a framework I'm trying to grow into the next big thing. It's not abandoned; it's not vibe-coded; it's not a thin wrapper over LangChain.

**What it is:** a substrate for teaching the eight architectural decisions, plus a library that implements them cleanly enough that you can use it for real work. fastai for agents.

If you want an agent you can own, audit, reproduce, teach, and — crucially — understand at the bottom of the stack, this is probably the smallest codebase in the world that gives you all five.

For what v0.3 specifically will *not* attempt, see
[`docs/v0.3-non-goals.md`](docs/v0.3-non-goals.md). Those are commitments, not
moods.

---

## This is a work repo, not a corpus

This repository holds **code**. It does not hold the planning and reporting
chain for the work done on it. There is no Statement of Work, no SOW directory,
and no filing chain in this tree, and there never should be:

- **`work_repo`** — this repository. Code that genuinely collides, so changes
  land on branches and get merged through pull requests.
- **`sow_repo`** — a separate corpus repository, elsewhere. Where work is
  scoped and reported.

They are different fields for a reason. If you came looking for a root
`SOW.md`, it is not missing — it was never supposed to be here. Read the code,
the [architecture doc](docs/architecture.md), and the
[CHANGELOG](CHANGELOG.md); those are the artifacts this repository owes you.

---

## Learn more

- 📖 [**`docs/architecture.md`**](docs/architecture.md) — the architectural decisions in detail
- 🧭 [**`chapters/`**](chapters/) — rebuild the framework yourself in 5 runnable chapters
- 🧪 [**`examples/`**](examples/) — 8 reference scenarios, each with a dataflow integrity audit
- 📋 [**`docs/API.md`**](docs/API.md) — semver contract for the public symbols
- 🚫 [**`docs/v0.3-non-goals.md`**](docs/v0.3-non-goals.md) — what v0.3 will not do
- 🌿 [**`docs/branch-consolidation-2026-08-22.md`**](docs/branch-consolidation-2026-08-22.md) — how the pre-v0.3 branches landed
- 📝 [**`CHANGELOG.md`**](CHANGELOG.md) — what shipped and when

---

## Contributing

Pull requests, issues, and architectural criticism are welcome. There is no
`CONTRIBUTING.md` yet; the contribution contract is `make verify` — apply, then
verify, then commit.

```bash
git clone https://github.com/zeroemployeeorg/sovereign-agent
cd sovereign-agent
make first-run          # install, preflight, sanity check
make test               # full deterministic suite
make demo-ch5           # see a working agent end-to-end
```

---

## Credits

**NanoClaw** (Gavriel Cohen) is the TypeScript reference implementation whose patterns — session-as-directory, group-queue serialization, tickets, filesystem IPC — sovereign-agent ports and extends in Python.

sovereign-agent is also built by reading and comparing production agent systems ([Claude Code](https://www.anthropic.com/news/claude-code), [OpenHands](https://github.com/All-Hands-AI/OpenHands), [Aider](https://github.com/paul-gauthier/aider)) and the foundational papers ([ReAct](https://arxiv.org/abs/2210.03629), [Reflexion](https://arxiv.org/abs/2303.11366), [SWE-agent](https://arxiv.org/abs/2405.15793), [Voyager](https://arxiv.org/abs/2305.16291), [MemGPT](https://arxiv.org/abs/2310.08560)). The pedagogical format is modelled on [nanoGPT](https://github.com/karpathy/nanoGPT) (Karpathy), [minitorch](https://github.com/minitorch/minitorch) (Rush), [LLMs-from-scratch](https://github.com/rasbt/LLMs-from-scratch) (Raschka), and [fastai](https://github.com/fastai/fastai) (Howard).

See [`CREDITS.md`](CREDITS.md) for full attributions.

---

## License

[Apache 2.0](LICENSE). Use commercially, modify, fork — just keep the notice.
