"""Build three separate, deterministic, self-contained companion downloads."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "book"
ASSETS = ("exercises", "solutions", "educator")
MANIFEST = ROOT / "docs/evidence/book-four-assets/archives-v1.json"
EXCLUDED = {"download.zip", "verification-v1.json", "archives-v1.json"}
DOWNLOAD_LINK = "[Download this complete asset](download.zip)"
README_TRANSFORM = "replace-download-link-with-extracted-notice-v1"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def members(asset: str) -> dict[str, bytes]:
    root = BOOK / asset
    result = {}
    for path in sorted(root.rglob("*")):
        if path.is_dir() or path.name in EXCLUDED or "__pycache__" in path.parts:
            continue
        assert path.is_file() and not path.is_symlink(), path
        result[str(path.relative_to(root))] = path.read_bytes()
    assert "README.md" in result
    readme = result["README.md"].decode()
    assert readme.count(DOWNLOAD_LINK) == 1, "source README must link its local download once"
    result["README.md"] = readme.replace(DOWNLOAD_LINK, "You have the complete asset.").encode()
    assert {f"ch{n:02d}/README.md" for n in range(1, 20)} <= set(result)
    for name, content in result.items():
        if name.endswith(".ipynb") and asset == "exercises":
            notebook = json.loads(content)
            assert notebook["metadata"]["course"]["instructor"] is False
            assert all(
                "instructor-check" not in cell.get("metadata", {}).get("tags", [])
                for cell in notebook["cells"]
            ), "worked checks leaked into the exercise download"
        if Path(name).name in {"README.md", "TEACHING-GUIDE.md", "SETUP.md"}:
            for destination in re.findall(r"\]\(([^)]+)\)", content.decode()):
                if destination.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                destination = destination.split("#", 1)[0]
                resolved = (root / name).parent.joinpath(destination).resolve()
                assert resolved.is_relative_to(root.resolve()), (asset, name, destination)
                relative = str(resolved.relative_to(root.resolve()))
                assert relative in result or any(
                    p.startswith(relative.rstrip("/") + "/") for p in result
                ), ("download navigation references an absent file", asset, name, destination)
    return result


def package() -> None:
    records = []
    for asset in ASSETS:
        content = members(asset)
        path = BOOK / asset / "download.zip"
        with ZipFile(path, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
            for name, data in sorted(content.items()):
                info = ZipInfo(name, date_time=(2026, 9, 9, 0, 0, 0))
                info.compress_type = ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                archive.writestr(info, data, compresslevel=9)
        records.append(
            {
                "asset": asset,
                "path": f"{asset}/download.zip",
                "sha256": digest(path.read_bytes()),
                "sourceReadmeSha256": digest((BOOK / asset / "README.md").read_bytes()),
                "readmeTransform": README_TRANSFORM,
                "members": {name: digest(data) for name, data in content.items()},
            }
        )
    MANIFEST.write_text(json.dumps({"schemaVersion": 1, "archives": records}, indent=2) + "\n")
    verify()


def verify() -> None:
    receipt = json.loads(MANIFEST.read_text())
    assert receipt["schemaVersion"] == 1
    records = receipt["archives"]
    assert len(records) == 3 and {row["asset"] for row in records} == set(ASSETS)
    for row in records:
        asset = row["asset"]
        assert row["path"] == f"{asset}/download.zip"
        path = BOOK / row["path"]
        assert digest(path.read_bytes()) == row["sha256"], "download bytes changed"
        assert row["sourceReadmeSha256"] == digest((BOOK / asset / "README.md").read_bytes())
        assert row["readmeTransform"] == README_TRANSFORM
        expected = members(asset)
        assert row["members"] == {name: digest(data) for name, data in expected.items()}
        with ZipFile(path) as archive:
            assert archive.testzip() is None
            assert len(archive.namelist()) == len(set(archive.namelist()))
            assert set(archive.namelist()) == set(expected), "download inventory drift"
            assert all(archive.read(name) == data for name, data in expected.items())
    print(
        "ACTIVE DOWNLOADS: exercise, solution and educator ZIPs; "
        "exact members and local navigation checked."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    verify() if parser.parse_args().verify else package()
