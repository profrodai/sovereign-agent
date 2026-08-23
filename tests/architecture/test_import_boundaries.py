"""Import-boundary tests for the ZeoCore / Sovereign capability split."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "src" / "sovereign_agent"

_FORBIDDEN_ZEOCORE = {
    ROOT / "contracts",
    ROOT / "errors.py",
}


def _imports_zeo_core(path: Path) -> list[str]:
    hits: list[str] = []
    files = [path] if path.is_file() else list(path.rglob("*.py"))
    for file in files:
        tree = ast.parse(file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "zeo_core" or alias.name.startswith("zeo_core."):
                        hits.append(f"{file}:{alias.name}")
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.module == "zeo_core" or node.module.startswith("zeo_core."):
                    hits.append(f"{file}:{node.module}")
    return hits


def test_runtime_evidence_contracts_do_not_import_zeocore() -> None:
    assert _imports_zeo_core(ROOT / "contracts") == []
    assert _imports_zeo_core(ROOT / "errors.py") == []


def test_capability_adapter_is_allowed_to_import_zeocore() -> None:
    hits = _imports_zeo_core(ROOT / "capabilities")
    assert hits, "adapter package must consume zeo_core"


def test_aliased_runtime_manifest_is_not_zeocore_manifest() -> None:
    from zeo_core.contracts import CapabilityManifest as ZeoManifest

    from sovereign_agent.contracts import RuntimeCapabilityManifest

    assert ZeoManifest is not RuntimeCapabilityManifest


def test_deprecated_runtime_evidence_aliases_warn() -> None:
    import warnings

    import sovereign_agent.contracts as contracts
    from sovereign_agent.contracts import RuntimeCapabilityManifest

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        alias = contracts.CapabilityManifest
    assert alias is RuntimeCapabilityManifest
    assert any(issubclass(item.category, DeprecationWarning) for item in caught)
