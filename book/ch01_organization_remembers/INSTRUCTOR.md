# Instructor note — Chapter 1: The organization remembers

## Teaching intent

This chapter establishes the single distinction the rest of the book leans
on: canonical state (SQLite) versus generated projection (Markdown, JSON
files under `governance/`). Every later governance claim — evidence,
acceptance, no-self-approval — is ultimately a claim about what SQLite
enforces, not what Python promises. If this chapter's boundary is fuzzy, the
learner will spend the rest of the book unsure which artifact to trust when
two disagree.

## Prerequisite knowledge

Chapter 0's vocabulary by exposure, not by definition: the learner has seen
`outcome`, `SOW`, `assignment`, `receipt` appear in output without a formal
definition yet (that's Chapter 2). This chapter does not require the learner
to define those terms correctly — it requires them to know where to look for
any of them.

## Likely misconceptions

- **"A rule enforced in Python is as good as a rule enforced in SQLite."**
  This chapter's own history directly refutes it: the first append-only guard
  used a SQLite session setting (`recursive_triggers`) the application turned
  on — and the guarantee lived in Python, not the database, so the raw
  `sqlite3` CLI silently bypassed it. Walk through this story explicitly, not
  just the fixed behavior; the failure is the lesson, not a footnote.
  Losing this before the trigger-based fix landed) as `SELECT * FROM events
  WHERE 1=0` — an omission is invisible, and this project caught it only by
  independently re-deriving each check rather than eyeballing.
- **"Append-only means tamper-proof."** It is explicitly not — Chapter 2's
  own exercise 6 covers this precisely (forged rows that agree with each
  other are still accepted), but plant the seed here: append-only stops
  rewriting a row, never stops adding a fabricated one.
- **"Deleting `governance/` is dangerous."** It is not — that is the entire
  point of the projection/canonical distinction. Have the learner actually
  run the deletion and confirm the organization still works before telling
  them the answer.

## Observation checkpoints

1. After the `.tables` listing: confirm the learner can name which three or
   four tables they'd check first to audit an outcome, before reading the
   provided table.
2. After the three append-only attempts (`UPDATE`, `DELETE`, `INSERT OR
   REPLACE`): confirm the learner notices all three are refused THE SAME
   WAY — by a database trigger, not by three different mechanisms.
3. After the transaction-rollback exercise: confirm the learner can state,
   without looking, that `before` and `after` were identical — the failure
   happened after inventory was written, and the whole point is that this is
   invisible from the outside.
4. After deleting `governance/`: confirm the learner predicted the outcome
   would still print correctly BEFORE running the command, not just observed
   it afterward.

## Discussion prompts

- "The database trigger fix needed no setting and held from any client. Why
  is 'holds from any client' a stronger property than 'holds from our own
  code'?"
- "Markdown is generated and never authoritative. What's a real-world
  analogy for a document that looks official but isn't the actual record?"
- "If SQLite and the filesystem can't update in one transaction, what's a
  concrete state this organization could end up in because of that gap?"
  (This previews the persistence-boundary doc's own honest limit.)

## Facilitation timing

Roughly 35-40 minutes guided: 10 minutes on Exercise 1 (tables and cash as a
ledger of movements), 10 minutes on Exercise 2 (the three append-only
attempts, including the recursive_triggers history), 10 minutes on Exercise 3
(the rollback script — run it live, don't just read the expected output),
5-10 minutes on Exercise 4 (canonical vs. projection) plus "Explain it back."

## Exercise debrief and assessment

A learner has landed this chapter if, given any specific fact about the
organization (inventory level, cash balance, whether a SOW is accepted), they
can immediately name which table or file is its authority — this is the
chapter's own stated bar ("which file or table is the authority for it — and
defend the answer"). The persistence-boundary doc's "the limit you must not
lie about" section is optional reading for a time-constrained session, but
should not be skipped entirely for a facilitator running the full course,
since Chapter 6 (recovery) directly depends on the learner already accepting
that a crash between two systems is a real, structural gap — not a bug to be
embarrassed about.
