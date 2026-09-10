# One book, four assets: migration record

**Created:** 2026-09-09 · **Status:** implementation of the operator's four-asset structure; added chapters remain planned

**Historical record — 2026-09-10:** Filename conventions are superseded by the [distribution update](book-distribution-20260910.md). Chapter links below now pin the original published revision so this record remains navigable; its numbering and historical descriptions are preserved.

The reader-facing publication is `book/README.md`. It routes to exactly four directories: `textbook`, `exercises`, `solutions` and `educator`. The canonical chapter registry is `book/textbook/BOOK.json`, with nineteen ordered entries, stable lesson IDs and explicit DRAFT or PLANNED status. The same numbers identify topics in all four assets.

## Which material is current

| Former location | Current home | Disposition |
|---|---|---|
| `book/` thirteen-chapter curriculum and labs | `docs/archive/book-20260909/` | Historical; removed from the active reading path |
| `book/always_on/chNN_*/README.md` | `book/textbook/chNN/README.md` using the map below | Current manuscript drafts with aligned navigation |
| `book/always_on/checkpoints`, appendices, learner files, skills and experiments | `book/textbook/` supporting material | Co-located with the teaching text |
| `book/always_on/practicals/ninety-minute-v1/chNN/student` | `book/exercises/chNN/` | Canonical student notebook and Markdown pairs |
| Corresponding `instructor` notebook pairs | `book/solutions/chNN/` | Canonical worked notebook and Markdown pairs |
| Corresponding `TEACHING-GUIDE.md` | `book/educator/chNN/` | Current guide with local student and worked copies |
| Earlier `classroom`, `exercises`, `educator` versions and old ZIPs | `docs/archive/book-20260909/always_on/` | Superseded editions retained unchanged; no competing active course |

No archived file is deleted or silently rewritten. The entire source snapshot comes from `profrodai/sovereign-agent@c72a580c1645042f94a56fa7e143938438a71d20`; all 686 file hashes and line counts were checked immediately after relocation. Existing commit-pinned downloads continue to refer to their original bytes.

## Numbering

| Previous chapter | Current chapter | Topic |
|---|---|---|
| 1 | [1](https://github.com/profrodai/sovereign-agent/blob/b4a0c56df9c74ace40f2b9e89b0fd659849087bc/book/textbook/ch01/README.md) | Make the first model call for Lucy |
| 2 | [2](https://github.com/profrodai/sovereign-agent/blob/b4a0c56df9c74ace40f2b9e89b0fd659849087bc/book/textbook/ch02/README.md) | Give the agent reliable shop tools |
| 3 | [3](https://github.com/profrodai/sovereign-agent/blob/b4a0c56df9c74ace40f2b9e89b0fd659849087bc/book/textbook/ch03/README.md) | Build the model and tool loop |
| 4 | [5](https://github.com/profrodai/sovereign-agent/blob/b4a0c56df9c74ace40f2b9e89b0fd659849087bc/book/textbook/ch05/README.md) | Remember across conversations |
| 5 | [6](https://github.com/profrodai/sovereign-agent/blob/b4a0c56df9c74ace40f2b9e89b0fd659849087bc/book/textbook/ch06/README.md) | Reuse a tested opening procedure |
| 6 | [8](https://github.com/profrodai/sovereign-agent/blob/b4a0c56df9c74ace40f2b9e89b0fd659849087bc/book/textbook/ch08/README.md) | Talk to the agent from your phone |
| 7 | [9](https://github.com/profrodai/sovereign-agent/blob/b4a0c56df9c74ace40f2b9e89b0fd659849087bc/book/textbook/ch09/README.md) | Wake up for schedules and stock events |
| 8 | [10](https://github.com/profrodai/sovereign-agent/blob/b4a0c56df9c74ace40f2b9e89b0fd659849087bc/book/textbook/ch10/README.md) | Ask permission before spending |
| 9 | [11](https://github.com/profrodai/sovereign-agent/blob/b4a0c56df9c74ace40f2b9e89b0fd659849087bc/book/textbook/ch11/README.md) | Survive the ambiguous supplier order |
| 10 | [12](https://github.com/profrodai/sovereign-agent/blob/b4a0c56df9c74ace40f2b9e89b0fd659849087bc/book/textbook/ch12/README.md) | Recover work after a process crash |
| 11 | [14](https://github.com/profrodai/sovereign-agent/blob/b4a0c56df9c74ace40f2b9e89b0fd659849087bc/book/textbook/ch14/README.md) | Isolate tools and untrusted content |
| 12 | [15](https://github.com/profrodai/sovereign-agent/blob/b4a0c56df9c74ace40f2b9e89b0fd659849087bc/book/textbook/ch15/README.md) | Measure whether the agent helps |
| 13 | [16](https://github.com/profrodai/sovereign-agent/blob/b4a0c56df9c74ace40f2b9e89b0fd659849087bc/book/textbook/ch16/README.md) | Improve behavior with evaluated changes |
| 14 | [17](https://github.com/profrodai/sovereign-agent/blob/b4a0c56df9c74ace40f2b9e89b0fd659849087bc/book/textbook/ch17/README.md) | Delegate one bounded task |
| 15 | [18](https://github.com/profrodai/sovereign-agent/blob/b4a0c56df9c74ace40f2b9e89b0fd659849087bc/book/textbook/ch18/README.md) | Deploy and maintain the agent |
| 16 | [19](https://github.com/profrodai/sovereign-agent/blob/b4a0c56df9c74ace40f2b9e89b0fd659849087bc/book/textbook/ch19/README.md) | Lucy leaves the shop for a day |

New Chapter 4 teaches durable SQLite state, Chapter 7 builds the work inbox and report outbox, and Chapter 13 builds MCP protocol integration separately from containment. Each has a detailed scope in the textbook and a clearly labelled planned entry in every companion. No empty notebook represents completed work. Existing isolation material still contains its MCP introduction until the new standalone chapter is authored; the construction brief states that extraction work explicitly.

## Notebook identity and self-contained use

Current `course.unit` metadata, visible chapter numbers and saved unit/handoff names use this edition's numbering. `source_unit` records the earlier practical identity. The compressed supplied runtime stays byte-identical; its internal `REFERENCE_LESSON` identifier selects the original exercise probe and is not the current book chapter number. This preserves the tested mechanism while preventing a renumbered chapter from accidentally selecting a different probe.

Each available notebook includes setup, specialist introductions and its teaching runtime. Students need Python 3.14 and Pydantic 2, not another book folder or an account. Solutions repeat the exercise context. Educator folders include exact local copies of both, so teachers can download one asset and prepare class. The textbook includes its front matter, chapters, code and appendices; its checkpoint setup uses the locked repository runtime, as stated in its setup instructions. The forthcoming from-scratch chapters must replace unexplained runtime dependencies with learner-owned construction; this navigation change alone does not prove that objective.

## Verification and downstream consumers

The [archive inventory](archive/book-20260909-inventory.json) binds every preserved path to its original file hash and line count. The archive gate also compares the original Git blobs when the pinned history is available. The active gate checks the four assets directly. Historical gates run in an explicit temporary projection of the archived book, and their results are labelled historical. They cannot certify the active notebooks. Current notebook execution, repeat runs, selected handoffs, Markdown parity and archive membership are verified separately. Student downloads exclude worked solutions; educator downloads contain both deliberately.

Website consumers must read `book/textbook/BOOK.json`, resolve paths relative to `book/textbook`, retain stable `lessonId` routing, and display PLANNED chapters without treating them as completed lessons. The old `book/always_on` source path is retired. The site repository previously projected an older source commit; this product migration does not claim the website has been re-synced or deployed. Existing thirteen/sixteen-chapter edition URLs must retain their old identity or point to an explicit migration notice, never silently change topics under an old chapter number.

Human review still decides whether the navigation and teaching are clear. Passing code checks does not certify classroom duration, comprehension or editorial quality. Manning remains a quality benchmark; publisher submission is outside this work.
