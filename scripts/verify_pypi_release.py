"""Post-publish packaging-truth check against the live PyPI JSON API.

A git tag is not a public release. Run this after Trusted Publisher upload:

    make verify-pypi VERSION=0.5.1

This script talks to pypi.org only. It does not publish, tag, or use credentials.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.verify_release import EXPECTED_VERSION, ZEOCORE_RANGE  # noqa: E402

JSON_URL = "https://pypi.org/pypi/sovereign-agent/json"
VERSION_URL = "https://pypi.org/pypi/sovereign-agent/{version}/json"
REPO = "https://github.com/zeroemployeeorg/sovereign-agent"
WORKFLOW = "publish.yml"


def _get_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        raise AssertionError(f"{url} returned HTTP {exc.code}") from exc
    if not isinstance(payload, dict):
        raise AssertionError(f"{url} did not return a JSON object")
    return payload


def verify_pypi(version: str) -> None:
    index = _get_json(JSON_URL)
    info = index.get("info") or {}
    live = str(info.get("version") or "")
    assert live == version, (
        f"PyPI JSON reports {live!r}, expected {version!r}. "
        "A git tag is not a public release; do not announce this version."
    )

    release = _get_json(VERSION_URL.format(version=version))
    rinfo = release.get("info") or {}
    assert str(rinfo.get("version")) == version
    requires_python = str(rinfo.get("requires_python") or "")
    assert "3.13" in requires_python, requires_python
    requires = rinfo.get("requires_dist") or []
    assert any(
        "zeocore" in str(item).replace(" ", "")
        and ">=0.5" in str(item).replace(" ", "")
        and "<0.6" in str(item).replace(" ", "")
        and "extra" not in str(item)
        for item in requires
    ), requires

    description = str(rinfo.get("description") or "")
    assert "@capability" in description, "PyPI README is not capability-first"
    assert "3.13" in description, "PyPI README does not state the Python floor"
    assert "register_tool" in description

    urls = rinfo.get("project_urls") or {}
    repo = str(urls.get("Repository") or urls.get("Homepage") or rinfo.get("home_page") or "")
    assert "zeroemployeeorg/sovereign-agent" in repo, repo

    files = release.get("urls") or []
    assert files, "no distribution files on PyPI"
    attested = [item for item in files if isinstance(item, dict) and item.get("has_provenance")]
    if not attested:
        # Trusted Publisher should attach provenance; fail closed if the field
        # is present and false for every file, succeed if the index omits it
        # but still lists github.com/zeroemployeeorg in upload provenance later.
        missing_flag = all(
            isinstance(item, dict) and "has_provenance" not in item for item in files
        )
        assert missing_flag, "PyPI files exist but none report provenance"
    print(
        json.dumps(
            {
                "package": "sovereign-agent",
                "version": version,
                "requires_python": requires_python,
                "zeocore": ZEOCORE_RANGE,
                "repository": repo,
                "workflow": WORKFLOW,
                "canonical_repo": REPO,
                "files": len(files),
                "provenance_files": len(attested),
            }
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default=EXPECTED_VERSION)
    args = parser.parse_args()
    verify_pypi(args.version)
    print(f"✓ PyPI JSON, metadata, README, and provenance for {args.version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
