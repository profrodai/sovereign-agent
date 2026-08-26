# `book/` is a content source, not a site

This directory is the source of truth for the Sovereign Agent textbook. It is
**designated** for rendering by the profrod.ai site. That integration does not
exist yet, so this document describes the contract a consumer will inherit, not
a pipeline you can observe running.

**This repository builds no site of its own.** It previously carried a MkDocs
configuration and a Documentation workflow; those existed only to produce a
second site nobody wanted, and were removed. Anything here that looks like a
publishing pipeline is gone deliberately — if you find one, it drifted back in.

## What a consumer can rely on

Each chapter is a directory `chNN_<slug>/` containing:

| File | Contract |
| --- | --- |
| `README.md` | the chapter, in Markdown, with the sections below |
| `solution.py` | runnable code that **imports the production package** rather than copying it |

Every chapter README carries these sections, in this order:

- `## Learning objective` — one concrete thing the reader will be able to do
- an exercise (`## The exercise` or `## Exercise N`)
- expected observations, with the **real output** of the commands shown
- `## Learner verification command` — how the reader checks their own work
- `## Explain it back` — questions with no lookup answer

## What is guaranteed, and by what

`scripts/verify_curriculum.py` runs in CI and fails the build if any of these
break:

- a required chapter is missing, or lacks any required section
- `solution.py` does not import the production package, or copies implementation
- **the exercise does not execute** — every runnable chapter is actually run
  against a fresh organization, not merely imported
- a chapter links to a file that does not exist
- a chapter references a `scripts/*.py` that does not exist
- a chapter claims Pulse behaviour, which does not exist before Unit 9

So a consumer inherits chapters whose **exercises execute**, whose links
resolve, and whose code imports what it says it imports.

### The limit, stated exactly

The gate executes each chapter's `solution.py` entry point. It does **not**
execute the commands shown in prose, and it does not compare displayed output
against a real run. Replacing `sovereign-agent doctor` in a fenced block with
`sovereign-agent definitely-not-a-command` leaves the gate reporting
`curriculum sound`. That was reproduced, not assumed.

An earlier version of this document claimed fenced commands were verified. They
are not, and a contract that overstates its own guarantee is worse than one
claiming less: a consumer would trust prose that nothing checks. What is checked
is the list above; what is not checked is this paragraph's subject.

## What a consumer must supply

Presentation. Ordering beyond the `chNN_` prefix. Any frontmatter its own
collection schema requires — this directory carries none, because frontmatter
belongs to the site that renders it, not to the source.

## Rendering notes

- Chapter cross-links are relative, of the form `../chNN_<slug>/README.md`.
- Links into `../../docs/` point at repository reference material and may need
  rewriting or dropping depending on what the site publishes.
- Fenced code blocks are real commands with real output, executed by hand when
  written. They are **not** verified by any gate — see the limit below — so
  render them verbatim rather than reformatting, and treat a mismatch between a
  block and reality as a bug worth reporting.

## Checking it yourself

```bash
python scripts/verify_curriculum.py
```

Exits 0 only when every statement in "What is guaranteed" holds. It says nothing
about the prose, by design and as stated above.
