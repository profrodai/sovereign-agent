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

Exits 0 when every chapter's python blocks all ran clean and every
python-then-text pair matched exactly. Exits 1 otherwise, printing every
failure found across every chapter -- not just the first.
"""

from __future__ import annotations

import contextlib
import io
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BOOK = REPO_ROOT / "book"
sys.path.insert(0, str(REPO_ROOT / "src"))

# Matches a fenced code block's opening line, capturing the language tag (may
# be empty) and, separately, tracks the block's start/end line numbers and
# body. Only the three-backtick style is used anywhere in book/.
FENCE_OPEN = re.compile(r"^```([\w-]*)\s*$")
FENCE_CLOSE = re.compile(r"^```\s*$")


@dataclass
class FencedBlock:
    lang: str  # the tag right after ``` -- "python", "text", "bash", or ""
    body: str  # the block's source, exactly as written between the fences
    start_line: int  # 1-based line number of the OPENING ``` fence


def parse_fenced_blocks(text: str) -> list[FencedBlock]:
    """Every fenced code block in a Markdown file, in document order.

    Deliberately simple line-scanning rather than a full Markdown parser:
    book/ READMEs use plain ``` fences with no nesting, and every existing
    chapter (see ch01-ch03) fits this. A block whose opening fence is never
    closed is silently ended at end-of-file rather than raising -- malformed
    fencing is a content bug for a human editor to notice by reading the
    chapter, not something this script exists to diagnose.
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
        # i now points at the closing fence (or len(lines) if unterminated)
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
    blocks = parse_fenced_blocks(text)

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
            with contextlib.redirect_stdout(captured):
                exec(compile(block.body, f"{chapter}:L{block.start_line}", "exec"), namespace)
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
    for chapter_dir in chapters:
        readme = chapter_dir / "README.md"
        python_count, pairs_checked, problems = check_chapter(readme)
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

    if all_problems:
        print(f"\n{len(all_problems)} book snippet problem(s).")
        return 1

    print(
        f"\nbook snippets sound: {len(chapters)} chapters, {total_python} python block(s) "
        f"executed, {total_pairs} text-pair(s) checked, all matched"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
