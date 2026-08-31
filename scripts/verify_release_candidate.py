#!/usr/bin/env python3
"""The Unit 12 release-candidate gate -- distinct from `verify_curriculum.py`.

`verify_curriculum.py` remains the structural gate: chapter structure,
sequence, instructor notes, frontmatter, rulings-index agreement, and
running each of the 13 exercises once against the SOURCE-TREE package. This
script does NOT re-implement or overload that scope (governing ruling
Holding 4; SOW section 3). It adds the release-specific surface instead:

1. Runs all 13 chapter exercises TWICE from fresh roots, against the
   source-tree package (matching the two-fresh-roots discipline
   `verify_curriculum.py`'s own gate already used, extended here to the
   release-candidate context specifically).
2. Builds the wheel, installs it into a clean Python 3.14 virtualenv OUTSIDE
   the source tree, and runs every chapter's exercise against THAT installed
   artifact -- not the source-tree package. A `sys.path` manipulation or an
   editable install anywhere on the way would silently exercise the source
   tree instead; this script proves the installed artifact is what actually
   ran by asserting the executing package's own `__file__` resolves inside
   the installed venv's site-packages, never inside this repository.
3. Mechanically validates the new Chapters 0-12 Andrea rubric's
   machine-checkable portions (`evaluate_andrea_chapters_0_12.py`).
4. Confirms `verify_proof_pack.py` passes against whatever manifest state
   exists at gate time.
5. Confirms no provider-status row claims LIVE_PASS without a real,
   verifiable evidence file backing it.
6. Confirms no committed evidence anywhere claims the real pilot-start act
   occurred (the local-pilot non-claim boundary), via the same grep-based
   discipline Unit 11's own "what this unit did not do" sections used.

    python scripts/verify_release_candidate.py

Exits 0 only when every stage above passes.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import venv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

# Reuse verify_curriculum.py's own chapter/entry-point tables rather than
# duplicating them -- a second, drifting copy of "13 chapters, 13 entry
# points" is exactly the kind of overlap the governing ruling's own
# instruction not to overload one script with another's responsibilities
# warns against; importing keeps this script's own chapter list a single
# source of truth shared with the structural gate, without adding any
# release-gate responsibility to that gate itself.
import verify_curriculum as curriculum_gate  # noqa: E402


def fail(failures: list[str], message: str) -> None:
    failures.append(message)


def run(argv: list[str], cwd: Path | None = None) -> tuple[int, str]:
    result = subprocess.run(  # noqa: S603 - fixed argv, no shell
        argv, capture_output=True, text=True, cwd=cwd or REPO_ROOT
    )
    return result.returncode, result.stdout + result.stderr


# ---------------------------------------------------------------------------
# Stage 1: all 13 exercises, twice, from fresh roots, source-tree package.
# ---------------------------------------------------------------------------


def run_exercises_twice_from_fresh_roots(failures: list[str]) -> None:
    import importlib.util

    for pass_number in (1, 2):
        for name in curriculum_gate.REQUIRED_CHAPTERS:
            entry_point = curriculum_gate.RUNNABLE.get(name)
            if entry_point is None:
                continue
            solution = REPO_ROOT / "book" / name / "solution.py"
            spec = importlib.util.spec_from_file_location(
                f"release_gate_{name}_pass{pass_number}", solution
            )
            if spec is None or spec.loader is None:
                fail(failures, f"pass {pass_number}: {name}: solution.py could not be loaded")
                continue
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
                function = getattr(module, entry_point)
                with tempfile.TemporaryDirectory() as scratch:
                    root = Path(scratch) / "root"
                    function(root, *curriculum_gate.RUNNABLE_ARGS.get(name, ()))
            except Exception as error:  # noqa: BLE001 - broken exercise, broken release
                fail(
                    failures,
                    f"pass {pass_number}: {name}: {entry_point}() failed against a fresh "
                    f"root: {type(error).__name__}: {error}",
                )


# ---------------------------------------------------------------------------
# Stage 2: build the wheel, install outside the source tree, run every
# exercise against the INSTALLED artifact, and prove it was actually used.
# ---------------------------------------------------------------------------


def build_and_install_wheel(failures: list[str], work_dir: Path) -> Path | None:
    dist_dir = work_dir / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    code, output = run(
        [sys.executable, "-m", "build", "--wheel", "-o", str(dist_dir)], cwd=REPO_ROOT
    )
    if code != 0:
        fail(failures, f"wheel build failed:\n{output}")
        return None
    wheels = sorted(dist_dir.glob("sovereign_agent-*.whl"))
    if not wheels:
        fail(failures, f"wheel build reported success but no wheel found in {dist_dir}")
        return None
    wheel = wheels[-1]

    venv_dir = work_dir / "venv"
    venv.EnvBuilder(with_pip=True, clear=True).create(venv_dir)
    venv_python = venv_dir / "bin" / "python"
    if not venv_python.is_file():
        fail(failures, f"venv creation did not produce {venv_python}")
        return None

    code, output = run([str(venv_python), "-m", "pip", "install", "--quiet", str(wheel)])
    if code != 0:
        fail(failures, f"installing the wheel into the clean venv failed:\n{output}")
        return None
    return venv_dir


def confirm_cli_from_installed_wheel(
    failures: list[str], venv_dir: Path, outside_root: Path
) -> None:
    sovereign_agent_bin = venv_dir / "bin" / "sovereign-agent"
    if not sovereign_agent_bin.is_file():
        fail(failures, f"installed wheel produced no {sovereign_agent_bin}")
        return

    code, output = run([str(sovereign_agent_bin), "--help"])
    if code != 0:
        fail(failures, f"installed `sovereign-agent --help` failed:\n{output}")

    code, output = run([str(sovereign_agent_bin), "doctor"])
    if code != 0:
        fail(failures, f"installed `sovereign-agent doctor` failed:\n{output}")

    code, output = run(
        [
            str(sovereign_agent_bin),
            "demo",
            "store",
            "--mode",
            "simulated",
            "--root",
            str(outside_root),
        ]
    )
    if code != 0 or "ACCEPTED" not in output:
        fail(failures, f"installed `sovereign-agent demo store` did not reach ACCEPTED:\n{output}")


def confirm_installed_package_is_actually_used(failures: list[str], venv_dir: Path) -> None:
    """The specific falsification this gate must catch: the installed-wheel
    exercise path silently falling back to the source-tree package instead
    of the installed one. Asks the VENV's OWN interpreter (never this
    process's `sys.path`, which already has `src/` prepended) where
    `sovereign_agent` resolves from, and refuses unless that path sits
    inside the venv's own site-packages and OUTSIDE this repository
    entirely.
    """
    venv_python = venv_dir / "bin" / "python"
    code, output = run(
        [
            str(venv_python),
            "-c",
            "import sovereign_agent, reference_organizations; "
            "print(sovereign_agent.__file__); print(reference_organizations.__file__)",
        ]
    )
    if code != 0:
        fail(failures, f"could not import the installed package from the clean venv:\n{output}")
        return
    lines = [line.strip() for line in output.strip().splitlines() if line.strip()]
    if len(lines) < 2:
        fail(failures, f"unexpected output resolving installed package location:\n{output}")
        return
    for module_name, resolved_path in zip(
        ("sovereign_agent", "reference_organizations"), lines, strict=True
    ):
        resolved = Path(resolved_path).resolve()
        inside_source_tree = True
        try:
            resolved.relative_to(REPO_ROOT.resolve())
        except ValueError:
            inside_source_tree = False

        if inside_source_tree:
            fail(
                failures,
                f"installed-wheel exercise path is NOT isolated from the source tree: "
                f"{module_name} resolved to {resolved}, inside {REPO_ROOT} -- this is exactly "
                "the silent source-tree fallback this gate exists to catch",
            )
            continue

        try:
            resolved.relative_to((venv_dir / "lib").resolve())
        except ValueError:
            fail(
                failures,
                f"{module_name} resolved to {resolved}, which is neither inside the "
                f"venv's own site-packages ({venv_dir / 'lib'}) nor inside the source tree -- "
                "cannot confirm the installed artifact is what actually ran",
            )


def run_all_exercises_against_installed_wheel(failures: list[str], venv_dir: Path) -> None:
    venv_python = venv_dir / "bin" / "python"
    for name in curriculum_gate.REQUIRED_CHAPTERS:
        entry_point = curriculum_gate.RUNNABLE.get(name)
        if entry_point is None:
            continue
        solution = REPO_ROOT / "book" / name / "solution.py"
        # Run each exercise's solution.py as a SUBPROCESS under the venv's
        # own interpreter -- with `src/` deliberately NOT on that
        # interpreter's sys.path -- so the only way `import sovereign_agent`
        # or `import reference_organizations` can succeed at all is via the
        # installed wheel. A fallback to the source tree would need `src/`
        # on sys.path, which this invocation never adds.
        args = curriculum_gate.RUNNABLE_ARGS.get(name, ())
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch) / "root"
            src_prefix = str(REPO_ROOT / "src")
            driver = (
                "import sys, json\n"
                "from pathlib import Path\n"
                f"sys.path = [p for p in sys.path if not p.startswith({src_prefix!r})]\n"
                "import importlib.util\n"
                f"spec = importlib.util.spec_from_file_location('m', {str(solution)!r})\n"
                "module = importlib.util.module_from_spec(spec)\n"
                "spec.loader.exec_module(module)\n"
                f"module.{entry_point}(Path({str(root)!r}), *{args!r})\n"
            )
            code, output = run([str(venv_python), "-c", driver], cwd=venv_dir)
        if code != 0:
            fail(
                failures,
                f"installed-wheel path: {name}: {entry_point}() failed: "
                f"{output.strip().splitlines()[-1] if output.strip() else code}",
            )


# ---------------------------------------------------------------------------
# Stage 3: the new Andrea rubric's machine-checkable portions.
# ---------------------------------------------------------------------------


def run_andrea_precheck(failures: list[str]) -> None:
    for script in ("evaluate_andrea_chapters_0_7.py", "evaluate_andrea_chapters_0_12.py"):
        code, output = run([sys.executable, str(REPO_ROOT / "scripts" / script)])
        if code != 0:
            fail(failures, f"{script} reported failing machine-checkable task(s):\n{output}")


# ---------------------------------------------------------------------------
# Stage 4: the proof-pack manifest, whatever state it is in right now.
# ---------------------------------------------------------------------------


def run_proof_pack_verifier(failures: list[str]) -> None:
    manifest_path = REPO_ROOT / "docs" / "evidence" / "unit12" / "proof-pack.json"
    if not manifest_path.is_file():
        fail(failures, f"no proof-pack manifest at {manifest_path}")
        return
    code, output = run([sys.executable, str(REPO_ROOT / "scripts" / "verify_proof_pack.py")])
    if code != 0:
        fail(failures, f"verify_proof_pack.py failed against the current manifest:\n{output}")


def confirm_no_false_live_pass(failures: list[str]) -> None:
    manifest_path = REPO_ROOT / "docs" / "evidence" / "unit12" / "proof-pack.json"
    if not manifest_path.is_file():
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    provider_status = manifest.get("provider_status", {})
    for provider, row in provider_status.items():
        if not isinstance(row, dict):
            continue
        if row.get("status") == "LIVE_PASS":
            evidence_path = row.get("evidence_path")
            if not evidence_path:
                fail(failures, f"provider_status.{provider}: LIVE_PASS with no evidence_path")
                continue
            resolved = (REPO_ROOT / "docs" / "evidence" / "unit12" / evidence_path).resolve()
            if not resolved.is_file():
                fail(
                    failures,
                    f"provider_status.{provider}: LIVE_PASS but evidence file "
                    f"{evidence_path!r} does not exist -- an unbacked LIVE_PASS claim",
                )


# ---------------------------------------------------------------------------
# Stage 5: no committed evidence anywhere claims the real pilot-start act.
# ---------------------------------------------------------------------------

# The exact reserved identifiers Unit 11's own closure ruling retired,
# unused, and named as never to be presented as evidence a real pilot began
# (docs/rulings/2026-08-30-unit11-local-closure-supersedes-real-deployment-gate.md,
# holding 5). Their presence anywhere in this unit's own committed evidence
# would itself be exactly the false claim this stage exists to catch.
RETIRED_REAL_PILOT_IDENTIFIERS = (
    "sovereign-store-pilot-001",
    "sovereign-store-30-day-v1",
)

REAL_PILOT_CLAIM_PATTERN = re.compile(
    r"\b(?:real|production)\b[^.\n]{0,80}\bpilot\b[^.\n]{0,40}\b(?:started|began|running|active)\b",
    re.IGNORECASE,
)


def confirm_no_real_pilot_claim(failures: list[str]) -> None:
    evidence_dir = REPO_ROOT / "docs" / "evidence" / "unit12"
    if not evidence_dir.is_dir():
        return
    for path in sorted(evidence_dir.rglob("*")):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for identifier in RETIRED_REAL_PILOT_IDENTIFIERS:
            if identifier in text:
                fail(
                    failures,
                    f"{path.relative_to(REPO_ROOT)}: contains the retired real-pilot "
                    f"identifier {identifier!r} -- this identifier authorizes nothing and "
                    "must never appear as evidence a real pilot began",
                )
        if REAL_PILOT_CLAIM_PATTERN.search(text):
            fail(
                failures,
                f"{path.relative_to(REPO_ROOT)}: text matches the shape of a real-pilot "
                "claim ('real/production pilot started/began/running/active')",
            )


def main() -> int:
    failures: list[str] = []

    print("Stage 1/6: all 13 exercises, twice, from fresh roots (source-tree package)...")
    run_exercises_twice_from_fresh_roots(failures)

    print("Stage 2/6: build wheel, install outside source tree, run every exercise against it...")
    with tempfile.TemporaryDirectory(prefix="sovereign-agent-release-gate-") as work:
        work_dir = Path(work)
        venv_dir = build_and_install_wheel(failures, work_dir)
        if venv_dir is not None:
            outside_root = work_dir / "outside-source-demo"
            confirm_cli_from_installed_wheel(failures, venv_dir, outside_root)
            confirm_installed_package_is_actually_used(failures, venv_dir)
            run_all_exercises_against_installed_wheel(failures, venv_dir)

    print("Stage 3/6: new Chapters 0-12 Andrea rubric, machine-checkable portions...")
    run_andrea_precheck(failures)

    print("Stage 4/6: proof-pack manifest verification...")
    run_proof_pack_verifier(failures)
    confirm_no_false_live_pass(failures)

    print("Stage 5/6: local-pilot non-claim boundary...")
    confirm_no_real_pilot_claim(failures)

    print("Stage 6/6: reporting...")
    for failure in failures:
        print(f"FAIL: {failure}")
    if failures:
        print(f"\n{len(failures)} release-candidate gate problem(s).")
        return 1
    print(
        "\nrelease candidate gate passed: 13 exercises pass twice from fresh roots, "
        "the installed wheel (proven isolated from the source tree) runs every exercise, "
        "the new Andrea rubric's machine-checkable portions pass, the proof-pack manifest "
        "verifies, no unbacked LIVE_PASS claim exists, and no evidence claims a real "
        "pilot-start act occurred."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
