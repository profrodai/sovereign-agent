# Sovereign Agent after v0.5

This is the public work-repository implementation plan. Binding authorization
remains in the Zero Employee corpus. This tree records code and repository
reality; it does not hold Statements of Work.

Recorded as of 2026-08-23:

- v0.4 established governed, durable single-node operation.
- v0.5.0 is tagged as the ZeoCore capability migration. A git tag is not a
  public release.
- v0.5.1 is the first truthful public 0.5 line (Python floor, ZeoCore
  constraint, README, and metadata agree). Do not announce v0.5 as published
  until that version is visible on PyPI.
- ZeoCore owns reusable capability definitions, schemas, guards, effects,
  requirements, concurrency declarations, projections, and invocation records.
- Sovereign Agent owns runtime commands, admission, approvals, locks,
  execution, sessions, providers, workers, delivery, and operational evidence.

The former document named “v0.5 production execution” is superseded. Its fleet
scope moves to v0.7. An immutable released version is not redefined after the
fact. The `v0.5.0` tag is not moved.

## Release sequence

| Release | Mission | Exit condition |
|---|---|---|
| v0.5 (landed) | Adopt ZeoCore as the reusable capability layer | Capability/runtime types are distinct and the compatibility path works |
| v0.6 | Complete and harden the capability-native single-node runtime | ZeoCore is the default authoring path, compatibility is proven, and PyPI artifacts are truthful |
| v0.7 | Add production worker and fleet control | Heterogeneous bounded workers execute with enforced policy and recoverable evidence |
| v0.8 | Unassigned evidence-gated release | Defined only after measured v0.7 deployments expose the next constraint |

v0.6 is a correctness release, not a fleet release. Distributed execution must
not compensate for unresolved single-node or package-contract defects.

## Cross-project boundary

Sovereign Agent may depend on ZeoCore's public package. ZeoCore must not depend
on Sovereign Agent. Neither package imports Zero Employee governance code.

```
zero-employee      authority, SOWs, policy, acceptance
       |
       v
sovereign-agent    runtime identity, execution, supervision, evidence
       |
       v
zeocore            reusable typed capability contracts and invocation semantics
```

A ZeoCore capability is not organizational authority, a seat, a worker, a
provider, an approval, or a runtime command. Runtime capacity never creates
authority.

## Version compatibility policy

- Sovereign Agent declares one tested ZeoCore minor range (`zeocore>=0.5,<0.6`).
- CI tests the minimum and newest allowed ZeoCore versions.
- A contract fixture pack must be executable from installed wheels, not only
  source trees.
- ZeoCore upgrades that change cancellation, serialization, projection, digest,
  effects, requirement, or invocation-record behavior require explicit
  compatibility review. See [compatibility.md](compatibility.md).
- Sovereign Agent wire schemas remain owned and versioned by Sovereign Agent
  even when they contain ZeoCore-derived evidence.
- Provider names are projections; canonical capability IDs are the durable
  identity.

The previous supported package pair is **sovereign-agent 0.2.0** (no ZeoCore,
Python 3.12) versus **sovereign-agent 0.5.1+** (`zeocore>=0.5,<0.6`, Python
3.13). That pair is recorded in the shipped fixture
`compatibility-matrix.json`.

## Packaging truth gate

A git tag is not a public release. Every release closes only after a clean
environment proves:

1. the exact version is visible from the PyPI JSON API;
2. wheel and sdist install on every supported Python version;
3. installed metadata includes the expected ZeoCore constraint;
4. installed contract fixtures pass without a repository checkout;
5. the README rendered by PyPI describes the released API and Python floor;
6. provenance points to the intended repository, tag, and workflow;
7. the previous supported package pair is included in the compatibility matrix.

Local proof (`make ready-to-ship`) covers items 2–5 and 7. After Trusted
Publisher upload, `make verify-pypi VERSION=<released>` covers items 1, 3, 5,
and 6 against the live index.

## Durable non-goals through v0.7

See [non-goals.md](non-goals.md). In short: no Sandcastle; no governance
decisions inside this package; no second reusable capability schema; no generic
workflow language; no Kubernetes/Nomad scheduler or cloud autoscaler; no
multi-region control plane; no general secrets or object-storage product; no
multi-repository atomic execution; no silent downgrade from requested isolation
or network policy.

## v0.8 rule

Do not pre-allocate v0.8 to fashionable infrastructure. After v0.7, collect
deployment receipts for at least two materially different installations and
file a new SOW in the corpus against the largest measured limitation. Candidate
topics may be high availability, richer artifact stores, or operator
experience, but none is authorized by this roadmap.
