# Test agents without spending tokens

Separate deterministic contract tests from live model evaluations. Most bugs in
capabilities, policies, session handling, and audits do not require a model call
to reproduce.

## Test capability behavior directly

Treat a capability like ordinary Python: construct its request, provide the
context expected by your application, and assert the structured result. Cover
validation failures, missing records, authorization, and external failures.

## Test a complete trajectory

The source repository includes a scripted client used by its own integration
tests:

- `tests/integration/test_end_to_end.py` shows a complete planner/executor run.
- `tests/integration/test_real_path_mocked.py` exercises live-path wiring with a
  mocked model.
- `tests/integration/test_examples.py` runs each example as a subprocess and
  checks meaningful output.

`FakeLLMClient` lives under `sovereign_agent._internal`; it is useful for
learning from this repository but is not covered by the public compatibility
contract. Applications should wrap their model boundary behind their own test
adapter rather than importing private APIs permanently.

## Test outcomes, not only exit codes

For each scenario, assert:

- the expected capabilities were called with valid arguments;
- required workspace artifacts exist;
- tickets and manifests verify;
- approval or policy decisions took the expected path;
- claims in the final answer came from recorded capability outputs.

The last check is dataflow integrity. It catches fluent answers that never used
the evidence.

## Keep live checks separate

Use a small opt-in suite for provider authentication and model behavior. Mark
it clearly, estimate cost, and never run it in default CI. In this repository:

```bash
make verify          # deterministic and offline
make ci-real-estimate
make ci-real-quick    # explicit network and token use
```

This split keeps the normal development loop fast and reproducible while still
detecting provider drift.
