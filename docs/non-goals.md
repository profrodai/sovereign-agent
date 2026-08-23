# Durable non-goals through v0.7

This document is normative for the v0.5–v0.7 sequence. A non-goal is removed
only by a corpus authorization that is then recorded in `CHANGELOG.md`. It is
not removed by a convenient pull request.

Read with [roadmap.md](roadmap.md) (sequence) and [API.md](API.md) (what is
promised). Historical v0.3 refusals that still hold are also in
[v0.3-non-goals.md](v0.3-non-goals.md).

## No Sandcastle

No Sandcastle dependency, adapter, service, or invocation path. The v0.3
prohibition in [v0.3-non-goals.md](v0.3-non-goals.md) remains in force through
v0.7.

## No governance decisions in this package

Sovereign Agent does not decide organizational authority, accept SOWs, or
interpret Zero Employee policy. It executes under evidence and admissions it
is given. ZeoCore also must not import Zero Employee governance code.

## No second reusable capability schema

Reusable actions are ZeoCore capabilities. This package does not grow a
parallel capability type system. Runtime evidence types
(`RuntimeCapabilityAssertion`, `RuntimeCapabilityManifest`) are not a second
authoring schema.

## No generic workflow language

No graph DSL, BPMN, or general-purpose workflow product. Session directories,
tickets, and runtime commands remain the execution model.

## No Kubernetes, Nomad, or cloud autoscaler

v0.7 may add production worker and fleet control on hosts the operator already
runs. It does not add a cluster scheduler or cloud autoscaler.

## No multi-region control plane

One control identity per deployment. Multi-region failover is not authorized
through v0.7.

## No general secrets or object-storage product

Credentials stay in operator-owned env/files. Artifacts stay in session
directories. This is not a secrets manager or an S3 competitor.

## No multi-repository atomic execution

A governed execution targets one configured repository identity. Cross-repo
atomic commits are out of scope.

## No silent isolation or network downgrade

If a caller requested a sandbox minimum or network policy, the runtime fails
closed rather than silently running weaker. `DockerWorker` remains a stub.

## How to change this list

1. File authorization in the Zero Employee corpus, not only in this repository.
2. Record the reversal in `CHANGELOG.md` under the release that reverses it,
   and edit this file in the same change.
3. Sandcastle remains refused through v0.7 without a corpus reversal.
