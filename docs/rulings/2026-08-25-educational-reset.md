# Ruling: Sovereign Agent 1.x educational reset

- **id:** `ruling-2026-08-25-educational-reset`
- **decided:** 2026-08-25
- **authority:** principal
- **applies_to:** Sovereign Agent 1.x and the `v1-educational` implementation line
- **status:** ACTIVE

This file is the work-repository record of the boundary-changing authorization
described in
[Sovereign Agent 1.0 — the executable textbook](../sows/sovereign-agent-v1-educational-control-plane.md).
The `v0.7.0` tag is not moved. Users who need the 0.x framework pin
`sovereign-agent<1`.

## Holdings

1. Sovereign Agent 1.x is the educational, executable reference for a
   Zero-Employee Organization.
2. It may contain the minimum governance necessary to teach and run an
   end-to-end outcome.
3. It is not the production control plane; the production destination is
   Zero Employee in Go.
4. The v0.7 public API compatibility promise ends at the 0.x release line.
   Version 1.0 may introduce a deliberately smaller API.
5. Sovereign Agent 1.x has exactly one direct runtime dependency: Pydantic.
6. Provider CLIs are external executables and are not Python package
   dependencies.
7. The existing `v0.7.0` tag remains immutable. Users who need the old
   framework pin `sovereign-agent<1`.

## Product choices recorded with this ruling

- **OQ-1 (resolved 2026-08-25):** Sovereign Agent 1.x may intentionally break
  the v0.7 public API and reposition the package as an executable textbook.
- **OQ-2 (resolved 2026-08-25):** the canonical executable is `sovereign-agent`.
  1.0 does not add a `sov` alias.
- **OQ-3 (resolved 2026-08-25):** teach **supervisor** as the runtime control
  loop. Use **service** only for operating-system lifecycle commands
  (`install`, `status`, `uninstall`). There is one supervisor; service is how
  that supervisor is hosted.

## Persistence (1.x)

JSON/TOML is canonical for committed governance; SQLite is canonical for
operational state; Markdown is generated.

## Consequences in this repository

- The 0.x non-goal “no governance decisions in this package” remains true for
  the v0.7 line and is superseded for 1.x by holding 2. See
  [non-goals.md](../non-goals.md).
- Implementation proceeds on `v1-educational`. `main` remains the 0.7 line
  until the 1.0 definition of done is met.
- The v0.7 public surface is mapped, not preserved, in
  [v1-removal-manifest.md](../v1-removal-manifest.md).
