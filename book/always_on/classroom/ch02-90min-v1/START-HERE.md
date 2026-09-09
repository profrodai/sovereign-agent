# Chapter 2 — ninety-minute classroom pack

**Created:** 2026-09-09 · **Status:** DRAFT teaching material, mechanically verified; classroom outcomes unobserved.

Open these **student** notebooks in order:

1. [Typed tools and trustworthy drafts](student/01-typed-tools-and-trustworthy-drafts-v1.ipynb) — minutes 0–45.
2. [Dispatch, permissions and transfer](student/02-dispatch-permissions-and-transfer-v1.ipynb) — minutes 45–90.

Each notebook is independently runnable. Neither requires a repository clone, a model key, an earlier notebook's files, a supplier account, or a paid service. Both contain all their code and fixture data. Start with functions, dictionaries, exceptions, and basic Python classes.

Use Jupyter or upload the notebooks to Google Colab. Use Python 3.10 or newer and Pydantic 2. If setup reports that Pydantic is missing or is version 1, run this in a separate notebook cell, then restart the kernel:

```python
%pip install "pydantic==2.13.4"
```

Installation needs internet; the lesson itself makes no network calls. Do not install the full Sovereign Agent package for this standalone class. The repository's cumulative runtime uses Python 3.14; these notebooks preserve the Chapter 2 implementation while spelling its multi-exception handler with parentheses for Python 3.10+ compatibility.

**Student Run All:** examples execute; deliberately unfinished exercises print `NEEDS_WORK` or `NOT_IMPLEMENTED`. Edit the marked exercise cells, then rerun their feedback cells. Those messages are expected learner feedback, not setup failures. A missing package, syntax exception, or traceback outside the exercise feedback is a setup/code problem to inspect.

**Instructor:** use [the 90-minute teaching guide](TEACHING-GUIDE.md) and the answer notebooks in `instructor/`. The worked answers and extra instructor cases are separate from the student ZIP. They are public teaching material, not tamper-proof exam secrets.

The four core exercises construct strict argument validation, calculate a grounded draft, repair permission and authority ordering, and connect a changed reservation rule to both stock reporting and draft validation. The second notebook also contains an extension bank for approximately 20–35 minutes of additional work.

Reference: [Give the agent reliable shop tools](https://www.profrod.ai/book/ch02-shop-tools). Embedded reference definitions come from `book/always_on/learner/ch02.py` at commit `4baba0a1c051d9d02af552b95a14a5b9c76f3f13`; each notebook records the exact source hash. The reservation factory is an explicitly labelled classroom extension. No model behavior or external purchase is claimed by these offline examples.

Suggested submission: both edited notebooks, the first predictions, and the four-question exit ticket. Keep anonymous classroom observations separately from student identities. The guide's times are a teaching plan, not measured learning outcomes.
