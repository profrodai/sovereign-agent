# Companion labs

These labs turn each chapter into a small, executable experiment faithfully
reduced from the real Sovereign Agent mechanisms. They are not alternative
implementations of the production system. Each lab maps its reduced mechanism
to exact production symbols and tests, then asks the learner to make its
observable invariants hold.

There is one directory for every chapter, with the same directory name as the
chapter. Every directory contains:

- `README.md`: the challenge and its production connection;
- `lab.json`: machine-readable production source and test references;
- `starter.py`: the learner's incomplete implementation;
- `solution.py`: the reference implementation;
- `check.py`: behavioral assertions shared by starter and solution; and
- `expected.json`: the deterministic observations from a correct solution.

Run the complete companion-lab gate from the repository root:

```console
python scripts/verify_book_labs.py
```

The gate intentionally runs the reference solution twice, each time with a
new temporary root. This catches examples that depend on leftover state or
produce nondeterministic observations. It also confirms that the starter fails
at the intended learning seam rather than accidentally behaving like another
solution.

## Author contract

`starter.py` and `solution.py` must expose:

```python
def exercise(root: Path) -> dict[str, object]: ...
```

The starter sets `STUDENT_TODO = True`, and its `exercise` raises
`NotImplementedError`. It also contains at least three distinct, numbered
implementation seams in the exact form `# TODO(1):`, `# TODO(2):`, and so on.
At least one top-level helper function or class besides `exercise` must give
the learner a meaningful decomposition to complete; a blank one-function
shell is not a lab. The solution sets `STUDENT_TODO = False`.

`check.py` must expose:

```python
def check(target_module: object, root: Path) -> dict[str, object]: ...
```

The checker calls `target_module.exercise(root)`, asserts the behavior the
student is meant to build, and returns a JSON-compatible dictionary of stable
observations. It must not special-case the reference solution. Its result for
the solution must equal `expected.json` exactly.

Each lab README must contain these second-level headings:

- `## Challenge`
- `## Production map`
- `## Run it`
- `## Break it`
- `## Explain it back`

`lab.json` uses schema version 1:

```json
{
  "schema_version": 1,
  "chapter": "ch00_first_shift",
  "title": "Trace the first shift",
  "production_sources": [
    "src/sovereign_agent/organization.py:Organization.accept"
  ],
  "production_tests": [
    "tests/test_control_plane.py::test_a_named_behavior"
  ],
  "entrypoint": "exercise",
  "expected": "expected.json"
}
```

Every production source is a repo-relative Python file followed by a class,
function, assignment, or qualified class member that actually exists in that
file. Production test nodes must name an existing test function (or
`Class::test_method`) in an existing file below `tests/`. `entrypoint` is
exactly `exercise`, and `expected` is exactly `expected.json`. Absolute paths, `..`
traversal, and symlink escapes are rejected. This makes every “production
map” inspectable rather than merely a claim in prose.

Keep outputs semantic and portable: report identifiers, states, counts, and
boolean invariants, not temporary paths, timestamps, random IDs, process IDs,
or platform-specific exception text. Use only the Python standard library in
lab infrastructure; exercising the installed project package is expected.
