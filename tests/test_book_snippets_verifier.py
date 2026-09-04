"""Regression tests for scripts/verify_book_snippets.py's fail-closed behaviour.

A Principal-level review found that the verifier's ``except Exception`` branch
does not catch ``SystemExit`` (it inherits from ``BaseException``, not
``Exception``): a chapter's python fence calling ``sys.exit(0)`` propagated
straight through ``check_chapter`` and ``main``'s per-chapter loop, and
terminated the whole process with exit code 0 -- silently, with no report,
and with every later chapter left unchecked. The same "silently stops early
and still looks green" family of bug existed in ``parse_fenced_blocks``: an
unterminated fence silently ended parsing (and therefore checking) of
everything after it in the file.

These tests build a synthetic, temporary ``book/`` directory (never touching
the real book/ch*/README.md files, which are a different party's content and
out of scope here) and monkeypatch the verifier module's ``BOOK`` constant to
point at it, so `check_chapter`/`main` run against fixtures instead of the
real book.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import time
import types
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "verify_book_snippets.py"


def _load_module() -> types.ModuleType:
    """Load scripts/verify_book_snippets.py as an importable module.

    scripts/ is not a package; this mirrors the importlib.util pattern
    scripts/verify_curriculum.py itself already uses to load a chapter's
    solution.py dynamically.
    """
    spec = importlib.util.spec_from_file_location("verify_book_snippets", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Register in sys.modules BEFORE exec_module: the script's FencedBlock is
    # a @dataclass under `from __future__ import annotations`, and dataclass
    # resolves its string annotations via sys.modules[cls.__module__] -- it
    # needs the module to already be findable there while its body executes.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_cli(cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run the real CLI entry point end to end, exactly as CI/Makefile do."""
    return subprocess.run(  # noqa: S603 - fixed argv, no shell
        [sys.executable, str(SCRIPT_PATH)], capture_output=True, text=True, cwd=cwd
    )


def _write_chapter(book: Path, name: str, readme_body: str) -> None:
    chapter_dir = book / name
    chapter_dir.mkdir(parents=True)
    (chapter_dir / "README.md").write_text(readme_body, encoding="utf-8")


# ---------------------------------------------------------------------------
# B2: SystemExit must not silently terminate the whole run.
# ---------------------------------------------------------------------------


def test_sys_exit_in_a_snippet_is_reported_not_swallowed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The exact defect: a python fence calling sys.exit(0) must be recorded
    as a problem for its own chapter, and must NOT end the whole run early --
    a later chapter in the same run must still be checked and reported.
    """
    book = tmp_path / "book"
    _write_chapter(
        book,
        "ch01_exits_early",
        "# Chapter 1\n\n```python\nimport sys\nsys.exit(0)\n```\n",
    )
    _write_chapter(
        book,
        "ch02_comes_after",
        '# Chapter 2\n\n```python\nprint("still alive")\n```\n\n```text\nstill alive\n```\n',
    )

    module = _load_module()
    monkeypatch.setattr(module, "BOOK", book)
    monkeypatch.setattr(module, "EXPECTED_CHAPTER_COUNT", 2)

    exit_code = module.main()

    assert exit_code == 1, "a chapter calling sys.exit(0) must not be reported as success"

    _, _, ch01_problems = module.check_chapter(book / "ch01_exits_early" / "README.md")
    assert len(ch01_problems) == 1
    assert "sys.exit(0)" in ch01_problems[0]
    assert "instead of completing" in ch01_problems[0]

    # The real proof execution continued: ch02, which comes AFTER the
    # sys.exit(0) chapter, still ran its own snippet and matched its own
    # expected output -- it was not skipped as collateral damage.
    ch02_python_count, ch02_pairs_checked, ch02_problems = module.check_chapter(
        book / "ch02_comes_after" / "README.md"
    )
    assert ch02_python_count == 1
    assert ch02_pairs_checked == 1
    assert ch02_problems == []


def test_sys_exit_reproduction_via_real_cli_subprocess(tmp_path: Path) -> None:
    """End-to-end: run the actual CLI (as CI and `make verify` do) against a
    fixture book with a chapter that calls sys.exit(0), and confirm the
    process itself exits 1 with a completion report -- not 0 with silence.

    This is the same shape as the Principal's original repro (prepending a
    sys.exit(0) fence to a real chapter and running the CLI), reproduced here
    as a fixture so it runs in CI rather than needing a one-off manual check.
    """
    book = tmp_path / "book"
    _write_chapter(
        book, "ch01_exits_early", "# Chapter 1\n\n```python\nimport sys\nsys.exit(0)\n```\n"
    )
    _write_chapter(
        book,
        "ch02_comes_after",
        '# Chapter 2\n\n```python\nprint("still alive")\n```\n\n```text\nstill alive\n```\n',
    )
    # The real script resolves BOOK from its own file location
    # (REPO_ROOT / "book"), not from cwd -- so exercise the same code by
    # copying the script next to the fixture book and running it there.
    fixture_script_dir = tmp_path / "scripts"
    fixture_script_dir.mkdir()
    fixture_script = fixture_script_dir / "verify_book_snippets.py"
    fixture_script.write_text(SCRIPT_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "src").mkdir()

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(fixture_script)], capture_output=True, text=True, cwd=tmp_path
    )

    assert result.returncode == 1, result.stdout + result.stderr
    assert "sys.exit(0)" in result.stdout
    assert "ch02_comes_after" in result.stdout
    assert "book snippets sound" not in result.stdout


# ---------------------------------------------------------------------------
# KeyboardInterrupt must NOT be swallowed -- it must still propagate as a
# real Ctrl-C would.
# ---------------------------------------------------------------------------


def test_keyboard_interrupt_is_not_swallowed_by_the_timeout_context(tmp_path: Path) -> None:
    """Raise KeyboardInterrupt synthetically inside code running under
    _block_timeout (rather than needing an actual human keypress) and confirm
    it propagates straight out uncaught -- proving the timeout's own
    signal-handling plumbing does not accidentally absorb a real interrupt
    either, independent of check_chapter's own except-clause ordering (which
    test_keyboard_interrupt_escapes_check_chapter_end_to_end covers).
    """
    module = _load_module()

    def _raises_interrupt() -> None:
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        with module._block_timeout(5):
            _raises_interrupt()


def test_keyboard_interrupt_escapes_check_chapter_end_to_end(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Same proof, but through the real check_chapter()/main() path: a
    chapter whose only python block raises KeyboardInterrupt must propagate
    it out of check_chapter uncaught, not record it as a snippet problem.
    """
    book = tmp_path / "book"
    _write_chapter(
        book,
        "ch01_interrupted",
        "# Chapter 1\n\n```python\nraise KeyboardInterrupt\n```\n",
    )
    module = _load_module()
    monkeypatch.setattr(module, "BOOK", book)

    with pytest.raises(KeyboardInterrupt):
        module.check_chapter(book / "ch01_interrupted" / "README.md")


# ---------------------------------------------------------------------------
# A hanging snippet must be caught by the timeout, not hang the verifier.
# ---------------------------------------------------------------------------


def test_hanging_snippet_is_caught_by_timeout_and_run_continues(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    book = tmp_path / "book"
    _write_chapter(
        book,
        "ch01_hangs",
        "# Chapter 1\n\n```python\nwhile True:\n    pass\n```\n",
    )
    _write_chapter(
        book,
        "ch02_comes_after",
        '# Chapter 2\n\n```python\nprint("still alive")\n```\n\n```text\nstill alive\n```\n',
    )
    module = _load_module()
    monkeypatch.setattr(module, "BOOK", book)
    monkeypatch.setattr(module, "EXPECTED_CHAPTER_COUNT", 2)
    # Use a short timeout so this test does not itself take BLOCK_TIMEOUT_SECONDS
    # (the production default) to run.
    monkeypatch.setattr(module, "BLOCK_TIMEOUT_SECONDS", 2)

    started = time.monotonic()
    exit_code = module.main()
    elapsed = time.monotonic() - started

    assert exit_code == 1
    assert elapsed < 15, "the hang must be bounded by the timeout, not run indefinitely"

    _, _, ch01_problems = module.check_chapter(book / "ch01_hangs" / "README.md")
    assert len(ch01_problems) == 1
    assert "did not finish within" in ch01_problems[0]

    ch02_python_count, ch02_pairs_checked, ch02_problems = module.check_chapter(
        book / "ch02_comes_after" / "README.md"
    )
    assert ch02_python_count == 1
    assert ch02_pairs_checked == 1
    assert ch02_problems == []


# ---------------------------------------------------------------------------
# B1 (coordinator-added): an unterminated fence must raise loudly, not
# silently truncate the rest of the chapter.
# ---------------------------------------------------------------------------


def test_unterminated_fence_raises_naming_chapter_and_line(tmp_path: Path) -> None:
    module = _load_module()
    text = (
        "# Chapter 1\n\n"
        "```python\n"
        "print('before the break')\n"
        "```\n\n"
        "```text\n"
        "before the break\n"
        "```\n\n"
        "```python\n"
        "print('this fence is never closed')\n"
    )
    with pytest.raises(module.UnterminatedFenceError) as excinfo:
        module.parse_fenced_blocks(text, chapter="ch99_broken")
    assert "ch99_broken" in str(excinfo.value)
    assert "line 11" in str(excinfo.value)


def test_unterminated_fence_in_one_chapter_is_reported_and_run_continues(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A malformed fence in one chapter must fail loudly for THAT chapter,
    but the run must still attempt and report every other chapter -- proving
    this is on the same "no silent early stop" footing as the SystemExit fix.
    """
    book = tmp_path / "book"
    _write_chapter(
        book,
        "ch01_broken_fence",
        "# Chapter 1\n\n```python\nprint('unterminated')\n",
    )
    _write_chapter(
        book,
        "ch02_comes_after",
        '# Chapter 2\n\n```python\nprint("still alive")\n```\n\n```text\nstill alive\n```\n',
    )
    module = _load_module()
    monkeypatch.setattr(module, "BOOK", book)
    monkeypatch.setattr(module, "EXPECTED_CHAPTER_COUNT", 2)

    exit_code = module.main()

    assert exit_code == 1
    with pytest.raises(module.UnterminatedFenceError):
        module.check_chapter(book / "ch01_broken_fence" / "README.md")

    ch02_python_count, ch02_pairs_checked, ch02_problems = module.check_chapter(
        book / "ch02_comes_after" / "README.md"
    )
    assert ch02_python_count == 1
    assert ch02_pairs_checked == 1
    assert ch02_problems == []


def test_well_formed_real_chapters_still_parse_with_chapter_kwarg() -> None:
    """The chapter= keyword added to parse_fenced_blocks must not disturb
    parsing of any currently well-formed real chapter."""
    module = _load_module()
    for readme in sorted((REPO_ROOT / "book").glob("ch*/README.md")):
        blocks = module.parse_fenced_blocks(
            readme.read_text(encoding="utf-8"), chapter=readme.parent.name
        )
        assert isinstance(blocks, list)


# ---------------------------------------------------------------------------
# Completion marker: main() must refuse to report success on a partial run.
# ---------------------------------------------------------------------------


def test_main_fails_loudly_if_fewer_chapters_were_attempted_than_expected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    book = tmp_path / "book"
    _write_chapter(
        book,
        "ch01_only_chapter",
        '# Chapter 1\n\n```python\nprint("hi")\n```\n\n```text\nhi\n```\n',
    )
    module = _load_module()
    monkeypatch.setattr(module, "BOOK", book)
    # Simulate the book claiming to have more chapters than actually exist,
    # standing in for the "some future escape exits the loop early" case this
    # count exists to catch defense-in-depth against.
    monkeypatch.setattr(module, "EXPECTED_CHAPTER_COUNT", 13)

    exit_code = module.main()

    assert exit_code == 1


def test_main_succeeds_when_attempted_count_matches_expected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    book = tmp_path / "book"
    _write_chapter(
        book,
        "ch01_only_chapter",
        '# Chapter 1\n\n```python\nprint("hi")\n```\n\n```text\nhi\n```\n',
    )
    module = _load_module()
    monkeypatch.setattr(module, "BOOK", book)
    monkeypatch.setattr(module, "EXPECTED_CHAPTER_COUNT", 1)

    assert module.main() == 0


# ---------------------------------------------------------------------------
# No regression: the real book must still verify exactly as before.
# ---------------------------------------------------------------------------


def test_real_book_chapters_still_pass_unchanged() -> None:
    result = run_cli(REPO_ROOT)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "book snippets sound: 13 chapters, 93 python block(s) executed" in result.stdout
    assert "83 text-pair(s) checked, all matched" in result.stdout
