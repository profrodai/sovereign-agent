# Migration from v0.7 to v1

Sovereign Agent 1.0 is a **new educational API**, not a compatible continuation
of the v0.7 fleet framework. Semver 1.0 records that break honestly. The
product identity remains Sovereign Agent.

## If you need the v0.7 framework

Pin the 0.x line:

```bash
pip install "sovereign-agent<1"
```

The git tag `v0.7.0` is immutable and is not moved by the 1.x work. See
[v0.7 maintenance](v0.7-maintenance.md).

## If you are starting in 1.x

Install from the 1.x line once it is published. The CLI remains
`sovereign-agent` (no `sov` alias). Concepts taught in 1.x are outcomes,
actors, providers, evidence, and acceptance—not `run_task`, ZeoCore
capabilities, fleet workers, or the 161-name v0.7 root API.

There is **no one-command import** from a v0.7 session directory into a 1.x
organization. Treat 1.x as a new project.

## Compatibility promise

| Line | Promise |
| --- | --- |
| `sovereign-agent<1` (v0.7.0) | Existing public `__all__` contract in [API.md](API.md) and [public-api-v0.7.txt](public-api-v0.7.txt) |
| `sovereign-agent>=1` | Deliberately smaller educational API; v0.7 names are not kept alive |

What is dropped, rewritten, or retained as a teaching concept is listed in
[v1-removal-manifest.md](v1-removal-manifest.md).

## Release strategy

- Branch `v1-educational` carries the 1.x implementation.
- `main` remains the 0.7 line until 1.0 meets its definition of done.
- Alpha wheels (`1.0.0a1` and later) may publish from the educational branch
  without merging to `main`.
- `1.0.0` publishes only after the educational reset ruling is active, the
  curriculum and store proof gates pass, and `main` is updated to the 1.x
  product.
