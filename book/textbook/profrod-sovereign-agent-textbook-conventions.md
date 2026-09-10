# Set up your reading and coding workspace

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Updated:** 2026-09-09 · **Status:** DRAFT

Read [the preface](profrod-sovereign-agent-textbook-preface.md) first. You need basic Python functions and classes, a terminal and a text editor. JSON, Pydantic, SQLite and each later library are introduced where they become useful; the planned foundations must be completed before this edition can claim an uninterrupted from-scratch path.

## Install the matching source environment

Download or clone the complete repository at the source revision supplied with your course. The textbook directory contains its manuscript, checkpoints, learner examples and appendix assets; Python dependencies and the supplied reference runtime live at the repository root. Copying this directory alone does not install those dependencies. Keep the root `pyproject.toml`, `uv.lock`, `src/`, `reference_organizations/`, `tests/` and `scripts/` with it.

Install Python and the dependencies from the committed lock, then run the first offline checkpoint from the repository root:

```bash
uv sync --frozen --python 3.14 --group dev
uv run --python 3.14 python book/textbook/checkpoints/profrod_sovereign_agent_ch01_first_model_call_checkpoint.py
```

`uv sync` creates the project environment; `--frozen` uses the checked-in dependency resolution. `uv run` executes inside that environment. Python 3.14 is required by some later listings. Chapter 1 walks through the model setup separately. Do not substitute the published package for the source checkout that accompanies this manuscript.

The first fixture should report the three stock items without contacting a model. Only run a chapter's `--live`, `--telegram` or container commands after completing the corresponding setup. No core checkpoint places a real supplier purchase.

## Keep reading, practice and answers separate

Read a textbook chapter before its matching [Exercise Book](../exercises/profrod-sovereign-agent-exercises-start-here.md) unit. Unit A builds and connects; Unit B diagnoses, repairs and transfers. Each unit budgets ninety minutes of dedicated work. Preserve your predictions and result before opening the [Solutions Book](../solutions/profrod-sovereign-agent-solutions-start-here.md). The [Educator Guide](../educator/profrod-sovereign-agent-educator-start-here.md) provides timing, demonstrations and assessment; it is not an extra prerequisite for self-study.

The completed `learner/profrod_sovereign_agent_ch02_pydantic_shop_tools_learner.py` and `learner/profrod_sovereign_agent_ch03_agent_loop_learner.py` files are supplied comparison copies. Save your own work at the paths named in those chapters, in your own checkout. The Chapter 3 checkpoint loads those definitions. Later reference checkpoints still import substantial supplied runtime code; [OWNERSHIP.md](profrod-sovereign-agent-textbook-ownership.md) identifies that boundary. A learner-owned cumulative package and its empty-workspace acceptance remain on the [construction roadmap](profrod-sovereign-agent-textbook-expansion.md).

## Read evidence labels literally

A code listing may depend on earlier definitions in the same chapter. Adjacent output states the expected observation; it does not make every fence a standalone program. Run examples from the repository root so relative fixture paths resolve. The [checkpoint index](profrod-sovereign-agent-textbook-checkpoints.md) lists the sixteen executable checkpoints and the three planned additions without pretending that a missing checkpoint ran.

| Evidence | Establishes | Does not establish |
| --- | --- | --- |
| Deterministic model fixture | Authored dispatch and failure paths | Live model choices or language quality |
| SQLite plus controlled supplier | Local state and independent simulated receipts | A different supplier's recovery contract |
| Real Telegram observation | The documented account and handset exchange | Continuous availability or fixture equivalence |
| Linux or container experiment | Behavior on the recorded host and configuration | A universal operating-system guarantee |
| Passing automated checks | The particular assertions executed | Reader comprehension or editorial acceptance |

A high score cannot change DRAFT to READY. Chapter 15 deliberately exposes a correct tool trace paired with a false explanation. Preserve failing cases and the exact source revision alongside successful results. Run `uv run python scripts/verify_book_assets_v2.py --textbook` for this manuscript's examples and checkpoints. The full repository gate is `make verify`; it also checks the other active assets and preserved historical material.

## Use Lucy's units and authority consistently

Stock quantities are whole tubs. Monetary records use integer pence, displayed as pounds only at the presentation boundary. Physical stock, pending replenishment, reserved spend and confirmed expenditure are distinct values. A remembered sentence is not an inventory record; an approval is not a purchase receipt.

Use synthetic shop data and the controlled supplier. Operator-owned configuration supplies credentials; keep tokens out of source, transcripts and evidence bundles. A skill grants no authority. An MCP child process has host privileges unless a separate execution boundary restricts it. Read the chapter's precise scope before interpreting a green result.

For each mechanism: predict the outcome, reproduce it, introduce the stated failure, repair it and change one constraint. Explain the changed behavior from the resulting records. [Reproducibility](appendices/profrod-sovereign-agent-textbook-reproducibility-v1.md) explains how to retain that evidence.

## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.
