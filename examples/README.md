# Examples

Nine scenarios demonstrate the framework end to end. Their default modes are
deterministic and make no model API calls. Run commands from the repository
root after `python -m pip install -e .`.

## Recommended order

| Example | What it teaches | Offline command | Live mode |
| --- | --- | --- | --- |
| `research_assistant` | First loop, typed lookup, grounding audit | `python -m examples.research_assistant.run` | `--real` |
| `pub_booking` | Loop and structured halves, policy handoff | `python -m examples.pub_booking.run` | `--real` |
| `capability_receipt` | Capability-native execution and receipts | `python -m examples.capability_receipt.run` | Offline only |
| `parallel_research` | Parallel-safe dispatch and timing | `python -m examples.parallel_research.run` | `--real` |
| `session_resume_chain` | Forward-only parent/child resume | `python -m examples.session_resume_chain.run` | `--real` |
| `classifier_rule` | Classifier-backed deterministic rule | `python -m examples.classifier_rule.run` | `--real` |
| `hitl_deposit` | Durable human approval, grant and deny | `python -m examples.hitl_deposit.run` | `--real` |
| `isolated_worker` | Landlock or macOS subprocess isolation | `python -m examples.isolated_worker.run` | `--real` |
| `code_reviewer` | Analyzer grounding and finding audit | `python -m examples.code_reviewer.run` | `--real` |

Each directory contains a README with expected behavior and output.

## Run everything offline

```bash
make examples
```

The examples are also subprocess-tested by
`tests/integration/test_examples.py`. A successful exit is not enough: tests
look for scenario-specific evidence.

## Live modes

Live modes require `NEBIUS_KEY` by default and can spend tokens:

```bash
cp .env.example .env
# edit .env
make ci-real-estimate
python -m examples.research_assistant.run --real
```

Live artifacts persist under the platform user-data directory printed by the
example. Override it with `SOVEREIGN_AGENT_DATA_DIR`.

## Platform and safety notes

- `isolated_worker` reports the policy available on the current host. Linux
  Landlock requires kernel 5.13+; macOS uses `sandbox-exec` where available.
- Docker and Podman execution require an engine and digest-pinned image.
- SSH execution requires pinned host identity and is covered in the operator
  docs rather than a beginner scenario.
- Real output is nondeterministic. Copy the audit pattern, not a particular
  model's prose.
