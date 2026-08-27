# Ruling: the book is published by `zeo-site`; this repository builds no site

- **id:** `ruling-2026-08-27-book-publication-destination`
- **decided:** 2026-08-27
- **authority:** principal
- **applies_to:** Sovereign Agent 1.x textbook publication
- **status:** ACTIVE

## The question

Where does the executable textbook get rendered and published, and what does
this repository owe that destination?

It was answered the expensive way. This repository carried a MkDocs
configuration and a Documentation workflow, aimed at building a second site.
That workflow had been failing on `main` across four merges. Repairing it
surfaced that GitHub Pages had never been enabled, which produced an escalation
asking the Principal to enable Pages — **to satisfy a gate that existed only
because the repairs had removed the earlier failure masking it.**

Nobody had asked whether this repository should publish a site at all. It should
not.

## Holdings

1. **`book/` is the single source of truth.** Prose and exercises stay together
   in one directory, so `scripts/verify_curriculum.py` keeps executing each
   chapter's exercise against the production package. Splitting prose from code
   would leave the gate testing something other than what a reader reads.
2. **`zeroemployeeorg/zeo-site` is the sole rendered, canonical home.** It owns
   presentation, ordering, navigation and any frontmatter its collection schema
   requires. Frontmatter belongs to the site, not the source.
3. **This repository builds no site.** No MkDocs, no Pages, no docs workflow.
   Double-indexing is avoided by construction rather than by convention: there
   is nothing here to index.
4. **Publication is not a Units 0–6 acceptance dependency.** What Units 0–6 owe
   is a *validated source* — chapters whose exercises execute, whose links
   resolve, and whose solutions import the production package. Whether a site
   has rendered them is the consuming repository's concern.
5. **The source names no consumer.** `book/CONTENT-SOURCE.md` states the
   contract a renderer inherits without naming which renderer. The destination
   is recorded here, in the ruling, because destinations change and contracts
   should not have to be edited when they do.

## Why holding 5 is not fussiness

An earlier draft of this work hardcoded the wrong destination in three files at
once. Sparring caught it before merge. Had the source named its consumer,
every future change of destination would require editing the contract — and a
contract edited for reasons unrelated to its subject is a contract nobody trusts.

## What this repository owes `zeo-site`

Exactly what `book/CONTENT-SOURCE.md` specifies, and nothing more:

- one directory per chapter, `chNN_<slug>/`, with `README.md` and `solution.py`
- the required sections in each chapter
- relative cross-links of the form `../chNN_<slug>/README.md`
- a gate that fails if an exercise stops executing, a link breaks, a referenced
  script disappears, or a solution stops importing the production package

## What it does not owe

Frontmatter, ordering metadata, rendered HTML, a navigation tree, or a build
step. Any of those appearing here is drift back toward the site this ruling
removed.

## How to check this ruling against the repository

```console
test ! -e mkdocs.yml && echo "no site config"
test ! -e .github/workflows/docs.yml && echo "no docs workflow"
grep -rl "mkdocs" pyproject.toml || echo "no mkdocs dependency"
python scripts/verify_curriculum.py
```

The last command is the one that matters: it is the guarantee `zeo-site`
inherits.
