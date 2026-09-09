# Chapter 2 student notebooks — 90 minutes


## New in v2: Pydantic from first principles

No previous Pydantic experience is assumed. Both notebooks and their matching Markdown copies contain the same complete introduction before the first tool model. Teach it once in notebook 1; in notebook 2, use it as a reference or as the starting lesson for learners joining there. Basic Python functions, dictionaries, exceptions and classes remain prerequisites.

The guided sequence moves from annotations that do not enforce types at runtime to `BaseModel`, required fields and defaults, structured `ValidationError` details, coercion versus strict validation, `Field` bounds, forbidden extra keys, and dictionary/JSON/schema representations. Worked examples ask for predictions before displaying actual values. A small data-repair exercise checks understanding before the original four core exercises. The final example shows why structurally valid data still needs an authoritative source and permission checks.

Allow 20 minutes for the primer, including its checkpoint. In the complete class, the opening stock problem takes 2 minutes and the primer occupies minutes 2–22. Its section times are relative to the primer's start. All later clock labels refer to the complete 90-minute lesson. The complete primer appears in notebook 2 for independent study; it is not a second 20-minute block in the class schedule.


Open 01-typed-tools-and-trustworthy-drafts-v2.ipynb first, then 02-dispatch-permissions-and-transfer-v2.ipynb. Notebook 1 takes 50 minutes, including a 20-minute Pydantic introduction; notebook 2 continues for 40 minutes. Each is independently runnable. If starting notebook 2 without Pydantic experience, work through its complete introduction first: allow 60 minutes including the 40-minute core.

Use Jupyter or upload to Google Colab. Python 3.10+ and Pydantic 2 are required. If setup asks for it, run `%pip install "pydantic==2.13.4"` in a separate cell and restart the kernel. No repository clone, model key, or paid account is needed. The installation needs internet; the lesson does not.

Run setup before class. Exercise starters deliberately print NEEDS_WORK or NOT_IMPLEMENTED. Edit each exercise cell and rerun its feedback. Preserve your first predictions. Your submission is both edited notebooks and the exit-ticket explanations.

The .md files contain the same lesson as readable text. They are a reading fallback, not a substitute for running your implementation. No instructor answer notebook or instructor-only transfer checks are included in this student archive.
