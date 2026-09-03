# Ruling: the book's rendered home is a section of `profrod-site`; this repository still builds no site

- **id:** `ruling-2026-09-03-book-publication-destination-is-profrod-site`
- **decided:** 2026-09-03
- **authority:** principal
- **applies_to:** Sovereign Agent 1.x textbook publication
- **status:** ACTIVE
- **supersedes:** `ruling-2026-08-27-book-publication-destination`

## What changed, and what did not

The 2026-08-27 ruling named `zeroemployeeorg/zeo-site` as the sole rendered,
canonical home for the book. That repository does not exist. The Operator has
since decided the actual destination: the Sovereign Agent book's rendered home
is a first-class section of `profrodai/profrod-site` (GitHub currently
resolves that reference to canonical `rodriveracom/profrod-site`), not a
second standalone documentation site and not a hand-copied manuscript.

This ruling records that decision on the source side. It changes the name of
the destination. It changes nothing about the source/consumer split, the
one-way exact-revision-bound consumption contract, or this repository's
refusal to build a site — those holdings were destination-agnostic when
written and remain correct under the new destination without modification.

Full account of the decision, its reasoning, and the required next actions for
every seat it names: `rodriveracom/org-zeroemployeeorg` issue #374 (Principal,
sovereign-agent, message `msg_238e8ab8-dd55-4e41-bb7d-b9d0670dd32a`,
2026-09-03T02:52:21Z). That filing is the substantive decision; this ruling
formalizes its source-side consequence in this repository's own record.

## Holdings

1. **`book/` remains the single source of truth.** Unchanged from the prior
   ruling's Holding 1. Prose and exercises stay together in one directory, so
   `scripts/verify_curriculum.py` keeps executing each chapter's exercise
   against the production package.
2. **`profrodai/profrod-site` is the selected rendered public home**,
   superseding the prior ruling's naming of `zeroemployeeorg/zeo-site`. It owns
   presentation, ordering, navigation, and any frontmatter its collection
   schema requires. The book must appear as a section of the existing site,
   not as a second standalone site and not as an independently editable copy.
3. **This repository still builds no site.** No MkDocs, no Pages, no docs
   workflow. Unchanged from the prior ruling's Holding 3.
4. **Publication is still not a curriculum acceptance dependency.** What the
   curriculum owes is a validated source — chapters whose exercises execute,
   whose links resolve, whose solutions import the production package.
   Whether a site has rendered them is the consuming repository's concern.
   Unchanged from the prior ruling's Holding 4.
5. **The source still names no consumer.** `book/CONTENT-SOURCE.md` states the
   contract a renderer inherits without naming which renderer, precisely so
   that this ruling — not that file — is what needed to change when the
   destination changed. This holding is validated by the change it just
   survived: `CONTENT-SOURCE.md` required no edit to remain accurate.
6. **Consumption is one-way and exact-revision-bound.** A site build imports
   or transforms the book from one full Sovereign Agent commit SHA. This
   repository does not track or assert what that SHA currently is; that
   assertion belongs to the consuming repository's build, which must expose
   its source version and refuse silent drift.
7. **No claim is made that the rendered section exists.** As of this ruling,
   `rodriveracom/profrod-site` is a private repository at a specific commit,
   and the profrod-site section is not yet built, deployed, or verified. The
   honest current reading home remains `profrodai/sovereign-agent/book/` until
   a rendered section passes the acceptance gates named in issue #374 item 5,
   including a human render checkpoint. A planned route is not a publication
   surface.

## What this repository owes the consumer

Exactly what `book/CONTENT-SOURCE.md` specifies, unchanged from the prior
ruling and independent of which repository consumes it:

- one directory per chapter, `chNN_<slug>/`, with `README.md` and `solution.py`
- the required sections in each chapter
- relative cross-links of the form `../chNN_<slug>/README.md`
- a gate that fails if an exercise stops executing, a link breaks, a
  referenced script disappears, or a solution stops importing the production
  package

## What it does not owe

Frontmatter, ordering metadata, rendered HTML, a navigation tree, a build
step, or knowledge of the consuming repository's visibility or deployment
state. Any of those appearing here is drift back toward the site the prior
ruling removed.

## How to check this ruling against the repository

```console
test ! -e mkdocs.yml && echo "no site config"
test ! -e .github/workflows/docs.yml && echo "no docs workflow"
grep -rl "mkdocs" pyproject.toml || echo "no mkdocs dependency"
python scripts/verify_curriculum.py
```

The last command is the one that matters: it is the guarantee any consumer
inherits, unchanged by which consumer it is.
