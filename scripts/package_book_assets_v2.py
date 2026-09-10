"""Package uniquely named teaching documents with source and community invitations."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

if __package__:
    from . import book_distribution_v1 as distribution
else:
    import book_distribution_v1 as distribution

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "book"
ASSETS = ("exercises", "solutions", "educator")
MANIFEST = ROOT / "docs/evidence/book-four-assets/archives-v2.json"
README_TRANSFORM = "replace-named-download-link-with-extracted-notice-v2"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def markdown_destinations(source: str) -> list[str]:
    """Ignore fenced examples, including shorter nested fences inside a long fence."""
    visible = []
    fence_character = ""
    fence_length = 0
    for line in source.splitlines():
        fence = re.match(r"^\s{0,3}(`{3,}|~{3,})(.*)$", line)
        if fence:
            marker, trailing = fence.groups()
            if not fence_character:
                fence_character, fence_length = marker[0], len(marker)
            elif (
                marker[0] == fence_character
                and len(marker) >= fence_length
                and not trailing.strip()
            ):
                fence_character, fence_length = "", 0
            continue
        if not fence_character:
            visible.append(line)
    return re.findall(r"\]\(([^)]+)\)", "\n".join(visible))


def members(asset: str) -> dict[str, bytes]:
    root = BOOK / asset
    result = {}
    for path in sorted(root.rglob("*")):
        if (
            path.is_dir()
            or path.suffix == ".zip"
            or path.name == "README.md"
            or "__pycache__" in path.parts
        ):
            continue
        assert path.is_file() and not path.is_symlink(), path
        assert path.name.startswith(distribution.PREFIX + "-"), path
        result[str(path.relative_to(root))] = path.read_bytes()
    start = distribution.start_name(asset)
    assert start in result, "download has no descriptively named starting point"
    source = result[start].decode()
    download_link = f"[Download this complete asset]({distribution.download_name(asset)})"
    assert source.count(download_link) == 1, "source start page must link its named download once"
    result[start] = source.replace(download_link, "You have the complete asset.").encode()
    assert {f"ch{n:02d}/{distribution.chapter_name(n, asset)}" for n in range(1, 20)} <= set(result)
    names = [Path(name).name.casefold() for name in result]
    assert len(names) == len(set(names)), "download members collide outside their directories"
    for name, content in result.items():
        if name.endswith(".ipynb"):
            notebook = json.loads(content)
            distribution.verify_attribution("".join(notebook["cells"][0]["source"]))
            if asset == "exercises":
                assert notebook["metadata"]["course"]["instructor"] is False
                assert all(
                    "instructor-check" not in cell.get("metadata", {}).get("tags", [])
                    for cell in notebook["cells"]
                ), "worked checks leaked into the exercise download"
        if name.endswith(".md"):
            distribution.verify_attribution(content.decode())
            for destination in markdown_destinations(content.decode()):
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
        path = BOOK / asset / distribution.download_name(asset)
        with ZipFile(path, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
            for name, data in sorted(content.items()):
                info = ZipInfo(name, date_time=(2026, 9, 10, 0, 0, 0))
                info.compress_type = ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                archive.writestr(info, data, compresslevel=9)
        records.append(
            {
                "asset": asset,
                "path": f"{asset}/{path.name}",
                "sha256": digest(path.read_bytes()),
                "sourceStartSha256": digest(
                    (BOOK / asset / distribution.start_name(asset)).read_bytes()
                ),
                "startTransform": README_TRANSFORM,
                "members": {name: digest(data) for name, data in content.items()},
            }
        )
    MANIFEST.write_text(json.dumps({"schemaVersion": 2, "archives": records}, indent=2) + "\n")
    verify()


def verify() -> None:
    receipt = json.loads(MANIFEST.read_text())
    assert receipt["schemaVersion"] == 2
    records = receipt["archives"]
    assert len(records) == 3 and {row["asset"] for row in records} == set(ASSETS)
    all_names: set[str] = set()
    for row in records:
        asset = row["asset"]
        assert row["path"] == f"{asset}/{distribution.download_name(asset)}"
        path = BOOK / row["path"]
        assert digest(path.read_bytes()) == row["sha256"], "download bytes changed"
        assert row["sourceStartSha256"] == digest(
            (BOOK / asset / distribution.start_name(asset)).read_bytes()
        )
        assert row["startTransform"] == README_TRANSFORM
        expected = members(asset)
        names = {Path(name).name.casefold() for name in expected}
        assert all_names.isdisjoint(names), "different audience packs share a filename"
        all_names.update(names)
        assert row["members"] == {name: digest(data) for name, data in expected.items()}
        with ZipFile(path) as archive:
            assert archive.testzip() is None
            assert len(archive.namelist()) == len(set(archive.namelist()))
            assert set(archive.namelist()) == set(expected), "download inventory drift"
            assert all(archive.read(name) == data for name, data in expected.items())
    print(
        "ACTIVE DOWNLOADS: three named packs; unique shared filenames, "
        "attribution and local navigation checked."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    verify() if parser.parse_args().verify else package()
