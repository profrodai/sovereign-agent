# Tutorial and chapter drift decision for v0.3

Decision: the five in-tree chapters remain the v0.2 teaching surface for the
v0.3.0 release. They are not expanded to teach the governed execution,
repository, relay, registry, or native-provider units.

This is intentional scope, not unnoticed drift:

- `tools/verify_chapter_drift.py` continues to prove that each chapter solution
  re-exports the v0.2 production primitive it teaches.
- The v0.2 symbols and behavior those chapters use remain in the v0.3 public API.
- v0.3 production features are taught by the numbered `docs/v0.3-unit*.md`
  implementation notes and API/migration documentation.
- The repository must not claim that chapters cover the entire production
  package. They cover the original five-chapter substrate.

A future teaching release may add governed-execution chapters. That work is not
part of v0.3.0 and will require its own drift mapping before documentation can
claim parity.
