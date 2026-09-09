# Authoring and verifying the ninety-minute practical course

**Created:** 2026-09-09 · **Updated:** 2026-09-09 · **Doctrinal basis:** CLAUDE.md Rev 17

Learners start at the [complete course index](ninety-minute-v1/START-HERE.md). That edition
contains two ninety-minute student units per chapter, their matching Markdown, separate worked
editions, sixteen teaching guides and thirty-four downloadable archives.

## Reproduce the current release

Use the repository's locked Python 3.14 development and authoring environments. No new dependency
is added by this course. The `.md` files inside each student and instructor directory are the
canonical notebook sources. Ordinary conversion preserves their authored content:

```bash
uv run --python 3.14 --group authoring python scripts/build_practical_course_v1.py
uv run --python 3.14 --group authoring python scripts/verify_practical_course_v1.py --execute
uv run --python 3.14 python scripts/package_practical_course_v1.py
make verify
```

The execution gate runs sixty-four notebooks in independent kernels, repeats each in one kernel,
and carries sixteen successful Unit A artifacts into separately started Unit B kernels. It checks
that imported teaching modules come from the embedded runtime, instructor holdouts pass and
untouched student work remains unfinished. `verification-v1.json` binds those observations to the
exact notebook and Markdown bytes. The normal gate verifies that receipt rather than launching
hundreds of kernels on every commit. The archive verifier compares every member with its source,
checks integrity and verifies separation of the student and instructor distributions.

## Author a successor edition

`authoring/` contains the first-principles Python, Pydantic, SQLite and chapter-specific teaching
text, plus independently specified changed-constraint cases and their worked solutions.
`build_practical_course_v1.py --author` was the initial assembly operation: it draws the core
construction/repair activities from the published exercise sources and embeds a frozen support
runtime from source basis `444c5f6`. `write_practical_guides_v1.py` assembles the chapter guides and
indices. These commands are authoring tools, not a learner setup step.

For a successor, give changed scripts and edition directories new versioned names. After initial
assembly, format and lint the Python cells with the locked Ruff toolchain, synchronize formatted
notebooks back to canonical Markdown with Jupytext, and perform ordinary conversion. Require an
exact byte-for-byte conversion check before execution. Inspect the actual lesson prose and worked
examples; formatting and execution do not assess explanations or measured learning outcomes.

Keep positive examples, refusals, new boundaries and predictions before solutions. Unit B's
reference start must remain visibly labelled; selecting a missing or invalid learner artifact
must fail without silently substituting a reference. Every new library or specialized concept
needs an introduction in both notebook and Markdown. Preserve the previous release and record
real classroom timing, hint use and transfer evidence when available.
