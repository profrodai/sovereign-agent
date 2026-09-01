#!/usr/bin/env python3
"""Check that a chapter's inline ```python``` snippets actually run, and that
any ```text``` block immediately following one is the REAL stdout that
snippet produces -- not prose someone typed and never re-checked.

Catches the ways an embedded "expected output" block rots:

- a `python` block that raises instead of running cleanly
- a `python` block whose captured stdout no longer matches the `text` block
  claimed to be its output (the code moved on; the printed transcript did not)
- a `text` block that was never actually validated against anything, because
  a human eyeballed it once at write time and nobody has re-run it since

Scope, deliberately narrow:

- Only ```python``` fenced blocks are executed. ```bash``` fenced blocks are
  shell/CLI transcripts, not Python -- this script skips them silently.
  Verifying those would mean actually invoking the CLI and filesystem, which
  is a separate, harder mechanism and out of scope here.
- A ```text``` block is checked ONLY when the fenced block immediately
  preceding it (the nearest fence before it in the document, ignoring any
  non-fenced prose in between) is a ```python``` block. A ```text``` block
  that follows a ```bash``` block, or any other fence, is skipped entirely --
  it is not this script's claim to verify, and it is not an error for one to
  exist there.
- Each chapter's python blocks execute cumulatively in ONE shared namespace,
  in document order -- later blocks may reference names (variables,
  functions, imports) an earlier block in the SAME chapter defined, which is
  how these chapters are actually written (ch01 opens a `:memory:` sqlite
  connection in one block and reuses it three blocks later). The namespace
  resets at the start of every new chapter. A later block reassigning a name
  an earlier block already used (rebinding `outcome["state"]`, redefining a
  function) is ordinary `exec()`-into-one-dict behaviour and needs no special
  handling: the dict is simply updated in place.
- An exception escaping a python block is a hard failure for that block. A
  python block that deliberately raises and catches its OWN exception inline
  (several ch01/ch02 blocks do exactly this, on purpose, to demonstrate a
  refusal) is not a failure -- only an exception that escapes the `exec` call
  is.
- `SystemExit` (e.g. a snippet calling `sys.exit(...)`) is treated exactly
  like any other escaping exception: a hard failure for that one block, and
  the loop moves on to the next block/chapter. `SystemExit` inherits from
  `BaseException`, not `Exception`, precisely so `sys.exit()` is NOT
  accidentally swallowed by ordinary code -- but a checker that lets a single
  chapter's snippet silently terminate the entire verification run (with exit
  code 0, no report, and every later chapter unchecked) is a worse failure
  mode than the one that design guards against. `KeyboardInterrupt` is the one
  `BaseException` this script does NOT treat as a snippet failure: a real
  Ctrl-C from whoever is running this tool is re-raised immediately and
  interrupts the tool, exactly as it would for any other Python program.
- Each python block runs under a wall-clock timeout (BLOCK_TIMEOUT_SECONDS).
  A snippet that hangs (an infinite loop, a blocking read with no data) is
  recorded as a problem for that block, the same way a raised exception is,
  and the run continues to the next block/chapter rather than hanging the
  whole verifier forever.

Exits 0 only when every chapter's python blocks all ran clean, every
python-then-text pair matched exactly, AND every chapter that exists under
book/ch* was actually attempted (see the completion-count assertion in
main()). Exits 1 otherwise, printing every failure found across every
chapter -- not just the first.
"""

from __future__ import annotations

import contextlib
import io
import re
import signal
import sys
from dataclasses import dataclass
from pathlib import Path
from types import FrameType

REPO_ROOT = Path(__file__).resolve().parent.parent
BOOK = REPO_ROOT / "book"
sys.path.insert(0, str(REPO_ROOT / "src"))

# Wall-clock ceiling for a single python fenced block. These are teaching
# snippets -- sqlite writes, small loops, string formatting -- not long
# computations; anything still running after this long is treated as hung.
BLOCK_TIMEOUT_SECONDS = 20

# The canonical count of chapters this repo currently ships. main() asserts
# it actually attempted exactly this many chapters before declaring success,
# so a future escape that exits the per-chapter loop early (some BaseException
# this script does not yet know to triage, a bug in the loop itself) fails
# loudly instead of reporting a partial run as if it were complete. Update
# this alongside REQUIRED_CHAPTERS in verify_curriculum.py when a chapter is
# added.
EXPECTED_CHAPTER_COUNT = 13


class SnippetTimeoutError(Exception):
    """Raised inside a python block's own execution when it runs past
    BLOCK_TIMEOUT_SECONDS. Deliberately a plain Exception (not BaseException):
    this is this script's own manufactured signal, not a real interruption,
    so it should be exactly as catchable/loggable as any other snippet
    failure -- there is nothing here a caller would need to specifically
    avoid catching, unlike KeyboardInterrupt.
    """


@contextlib.contextmanager
def _block_timeout(seconds: int):  # type: ignore[no-untyped-def]
    """Bound a single `exec()` call to `seconds` of wall-clock time.

    Uses SIGALRM rather than a thread or a subprocess:

    - A thread cannot be forcibly killed in Python. A hung snippet's thread
      would leak for the rest of the process's life, and -- worse -- it could
      keep mutating the shared per-chapter `namespace` dict concurrently with
      whatever runs after the timeout fires, which is exactly the kind of
      silent corruption this hardening pass exists to remove.
    - A subprocess (or `multiprocessing`) can be forcibly killed cleanly, but
      this script's whole design is a SHARED, cumulative namespace across a
      chapter's blocks (ch01 opens a `:memory:` sqlite connection in one
      block and reuses it three blocks later) -- and that namespace holds
      objects (open sqlite connections, etc.) that do not survive a pickle
      across a process boundary. Moving to a subprocess per block would mean
      re-architecting the thing this checker exists to verify, not just
      adding a timeout to it.
    - `signal.alarm` needs no new process/thread model, runs entirely within
      the existing single-process, single-threaded `exec()` call, and raises
      a normal, catchable Python exception at the interrupted instruction --
      which slots directly into the same "problem for this block, continue to
      the next" handling already used for every other snippet failure.

    Trade-off, stated plainly: `signal.alarm` is POSIX-only (no Windows) and
    only fires on the main thread. This script runs as a CI/maintainer gate
    on Linux (see .github/workflows/ci.yml: ubuntu-latest) invoked from the
    main thread, so that trade-off costs nothing in this tool's actual
    environment. If this script is ever run on Windows or off the main
    thread, this guard degrades to a no-op timeout (the alarm is simply not
    scheduled) rather than raising an unrelated platform error -- a hung
    snippet there would hang the run, same as before this hardening pass, but
    every other platform this tool is actually used on is protected.
    """
    has_alarm = hasattr(signal, "SIGALRM") and hasattr(signal, "alarm")
    if not has_alarm:
        yield
        return

    def _on_alarm(signum: int, frame: FrameType | None) -> None:
        raise SnippetTimeoutError(f"execution exceeded {seconds}s")

    previous_handler = signal.signal(signal.SIGALRM, _on_alarm)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous_handler)


# Matches a fenced code block's opening line, capturing the language tag (may
# be empty) and, separately, tracks the block's start/end line numbers and
# body. Only the three-backtick style is used anywhere in book/.
FENCE_OPEN = re.compile(r"^```([\w-]*)\s*$")
FENCE_CLOSE = re.compile(r"^```\s*$")


class UnterminatedFenceError(Exception):
    """A ``` fence was opened but never closed before end-of-file."""


@dataclass
class FencedBlock:
    lang: str  # the tag right after ``` -- "python", "text", "bash", or ""
    body: str  # the block's source, exactly as written between the fences
    start_line: int  # 1-based line number of the OPENING ``` fence


def parse_fenced_blocks(text: str, *, chapter: str = "<unknown>") -> list[FencedBlock]:
    """Every fenced code block in a Markdown file, in document order.

    Deliberately simple line-scanning rather than a full Markdown parser:
    book/ READMEs use plain ``` fences with no nesting, and every existing
    chapter (see ch01-ch03) fits this. A block whose opening fence is never
    closed raises UnterminatedFenceError naming the chapter and the opening
    fence's line number, rather than silently ending the block (and every
    fence after it) at end-of-file -- a malformed fence used to mean every
    block past that point in the file went unparsed and unchecked with no
    error and no warning, which is the same "false green from silently
    stopping early" failure family as an escaping SystemExit.
    """
    blocks: list[FencedBlock] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        match = FENCE_OPEN.match(lines[i])
        if match is None:
            i += 1
            continue
        lang = match.group(1)
        start_line = i + 1  # 1-based
        body_lines: list[str] = []
        i += 1
        while i < len(lines) and not FENCE_CLOSE.match(lines[i]):
            body_lines.append(lines[i])
            i += 1
        if i >= len(lines):
            raise UnterminatedFenceError(
                f"{chapter}: fence opened at line {start_line} is never closed "
                f"(reached end of file while still inside it)"
            )
        # i now points at the closing fence.
        blocks.append(FencedBlock(lang=lang, body="\n".join(body_lines), start_line=start_line))
        i += 1
    return blocks


def normalize(text: str) -> str:
    """Strip trailing whitespace from each line and from the whole block, so
    a trailing-newline or trailing-space difference is not a false failure,
    while a real content difference still is.
    """
    lines = [line.rstrip() for line in text.splitlines()]
    return "\n".join(lines).strip()


def check_chapter(readme: Path) -> tuple[int, int, list[str]]:
    """Run one chapter's python blocks cumulatively and check its
    python-then-text pairs. Returns (python_blocks_found, text_pairs_checked,
    problems).
    """
    chapter = readme.parent.name
    text = readme.read_text(encoding="utf-8")
    blocks = parse_fenced_blocks(text, chapter=chapter)

    problems: list[str] = []
    namespace: dict[str, object] = {}
    python_block_count = 0
    pairs_checked = 0

    for index, block in enumerate(blocks):
        if block.lang != "python":
            continue
        python_block_count += 1

        captured = io.StringIO()
        try:
            with _block_timeout(BLOCK_TIMEOUT_SECONDS), contextlib.redirect_stdout(captured):
                exec(compile(block.body, f"{chapter}:L{block.start_line}", "exec"), namespace)
        except KeyboardInterrupt:
            # A real Ctrl-C from whoever is running this tool. Re-raise
            # IMMEDIATELY, before appending to problems, before touching the
            # loop, before anything else -- this must interrupt the tool the
            # same way it would interrupt any other Python program, not be
            # recorded as a snippet failure and quietly continue.
            raise
        except SnippetTimeoutError as error:
            problems.append(
                f"{chapter}: python block at line {block.start_line} did not finish within "
                f"{BLOCK_TIMEOUT_SECONDS}s ({error}) -- treated as hung and skipped"
            )
            continue
        except SystemExit as error:
            problems.append(
                f"{chapter}: python block at line {block.start_line} called "
                f"sys.exit({error.code!r}) instead of completing"
            )
            # Same reasoning as the Exception branch below: a following text
            # block would be compared against a run that never finished, so
            # skip the pair check and move on to the next python block.
            continue
        except Exception as error:  # noqa: BLE001 - any escape is the failure this catches
            problems.append(
                f"{chapter}: python block at line {block.start_line} raised "
                f"{type(error).__name__}: {error}"
            )
            # Still check for a following text block would compare against a
            # run that never finished -- skip the pair check for this block
            # and move on to the next python block in the same chapter. The
            # namespace already holds whatever the block managed to define
            # before raising, matching real REPL behaviour.
            continue
        except BaseException as error:  # noqa: BLE001 - catches GeneratorExit and anything
            # else that is a BaseException but neither KeyboardInterrupt (re-raised above,
            # unconditionally, before this) nor SystemExit (its own clause above, for a
            # clearer message) nor an ordinary Exception (the clause above this one). This
            # is deliberately last and deliberately broad: the entire point of this
            # hardening pass is that NO escape from a snippet's exec() -- of any kind --
            # is allowed to propagate out of check_chapter() and silently end the run.
            problems.append(
                f"{chapter}: python block at line {block.start_line} raised "
                f"{type(error).__name__}: {error} (a BaseException, not caught by Exception)"
            )
            continue

        # A python-then-text pair exists only when the VERY NEXT fenced
        # block (ignoring only non-fenced prose -- there is no such thing
        # here since parse_fenced_blocks already skips prose) is tagged
        # text. If the next fence is bash, another python block, or
        # anything else, there is no pair to check -- skip silently.
        next_block = blocks[index + 1] if index + 1 < len(blocks) else None
        if next_block is None or next_block.lang != "text":
            continue

        pairs_checked += 1
        expected = normalize(next_block.body)
        actual = normalize(captured.getvalue())
        if expected != actual:
            problems.append(
                f"{chapter}: python block at line {block.start_line} output does not match "
                f"the text block at line {next_block.start_line}\n"
                f"--- expected (text block) ---\n{expected}\n"
                f"--- actual (captured stdout) ---\n{actual}\n"
                f"--- end ---"
            )

    return python_block_count, pairs_checked, problems


def main() -> int:
    chapters = sorted(p for p in BOOK.glob("ch*") if (p / "README.md").is_file())
    if not chapters:
        print("BOOK SNIPPETS: no chapters found under book/ch*")
        return 1

    all_problems: list[str] = []
    report_rows: list[str] = []
    total_python = 0
    total_pairs = 0
    chapters_attempted = 0
    for chapter_dir in chapters:
        readme = chapter_dir / "README.md"
        try:
            python_count, pairs_checked, problems = check_chapter(readme)
        except UnterminatedFenceError as error:
            # The chapter WAS attempted -- parsing started and failed loudly,
            # which is exactly the point: this is a reported problem for this
            # chapter, not a silent truncation, and the loop still moves on
            # to check every remaining chapter.
            chapters_attempted += 1
            all_problems.append(str(error))
            report_rows.append(f"  {chapter_dir.name}: FAIL -- {error}")
            continue
        chapters_attempted += 1
        all_problems.extend(problems)
        total_python += python_count
        total_pairs += pairs_checked
        status = "FAIL" if problems else "ok"
        report_rows.append(
            f"  {chapter_dir.name}: {python_count} python block(s), "
            f"{pairs_checked} text-pair(s) checked -- {status}"
        )

    for problem in all_problems:
        print(f"BOOK SNIPPETS: {problem}")

    print()
    print("book snippet report:")
    for row in report_rows:
        print(row)

    # Defense in depth: even after the BaseException triage above, assert the
    # loop actually reached every chapter it should have, rather than trusting
    # that no future escape can ever exit it early. An early, unreported exit
    # from this loop is precisely how the original SystemExit defect looked
    # green (exit 0, no output) -- this makes a partial run impossible to
    # mistake for a complete one, even from a cause this script does not yet
    # know to name.
    if chapters_attempted != len(chapters):
        print(
            f"\nBOOK SNIPPETS: INCOMPLETE RUN -- attempted {chapters_attempted} of "
            f"{len(chapters)} discovered chapter(s). A verification run that does not "
            f"finish must never be reported as passing."
        )
        return 1
    if chapters_attempted != EXPECTED_CHAPTER_COUNT:
        print(
            f"\nBOOK SNIPPETS: attempted {chapters_attempted} chapter(s), but "
            f"EXPECTED_CHAPTER_COUNT in this script is {EXPECTED_CHAPTER_COUNT}. Update "
            f"EXPECTED_CHAPTER_COUNT in scripts/verify_book_snippets.py to match the "
            f"book's real chapter count (this guards against BOOK.glob('ch*') silently "
            f"discovering fewer chapters than the book actually has, e.g. a chapter "
            f"directory renamed or misplaced outside book/)."
        )
        return 1

    if all_problems:
        print(f"\n{len(all_problems)} book snippet problem(s).")
        return 1

    print(
        f"\nbook snippets sound: {chapters_attempted} chapters, {total_python} python block(s) "
        f"executed, {total_pairs} text-pair(s) checked, all matched"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
