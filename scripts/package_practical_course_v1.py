"""Build deterministic, separate student and instructor practical archives."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parent.parent
EDITION = ROOT / "book/always_on/practicals/ninety-minute-v1"
MANIFEST = EDITION / "archives-v1.json"


def start_text(chapters, instructor):
    lines = [
        "# Ninety-minute book practicals",
        "",
        "Two units per chapter; each unit is planned for 90 minutes of dedicated work.",
        "Use Python 3.14 and Pydantic 2 in Jupyter. No repository clone or API key is needed.",
        'If needed, install with `%pip install "pydantic==2.13.4"` and restart the kernel.',
        "Basic Python functions, loops, conditions, lists and dictionaries are prerequisites.",
        "Every notebook introduces its specialized concepts and includes its teaching runtime.",
        "",
        "Start with the student notebook. NEEDS_WORK means an exercise is still unfinished.",
        "Unit B includes a labelled reference start. Set LEARNER_HANDOFF to your saved Unit A",
        "artifact to use your own successful work. Save notebooks and practical-work evidence.",
        "",
    ]
    for chapter in chapters:
        prefix = f"ch{chapter:02d}"
        lines.append(f"## Chapter {chapter}")
        lines.append("")
        for letter in "ab":
            stem = f"{prefix}/student/unit-{letter}-v1"
            lines.append(
                f"- Unit {letter.upper()}: [notebook]({stem}.ipynb) · [Markdown]({stem}.md)"
            )
        if instructor:
            lines.append(f"- [Teaching guide]({prefix}/TEACHING-GUIDE.md)")
            for letter in "ab":
                stem = f"{prefix}/instructor/unit-{letter}-v1"
                lines.append(
                    f"- Worked {letter.upper()}: [notebook]({stem}.ipynb) · [Markdown]({stem}.md)"
                )
        lines.append("")
    lines.extend(
        [
            "Duration is a teaching plan, not a measured classroom outcome. Offline scenarios do",
            "not certify live services, phone delivery, OS containment or deployment.",
            "",
        ]
    )
    return "\n".join(lines).encode()


def members(chapters, instructor):
    result = {"START-HERE.md": start_text(chapters, instructor)}
    for chapter in chapters:
        prefix = f"ch{chapter:02d}"
        for edition in ["student", "instructor"] if instructor else ["student"]:
            for letter in "ab":
                for extension in ("md", "ipynb"):
                    name = f"{prefix}/{edition}/unit-{letter}-v1.{extension}"
                    result[name] = (EDITION / name).read_bytes()
        if instructor:
            name = f"{prefix}/TEACHING-GUIDE.md"
            result[name] = (EDITION / name).read_bytes()
    return result


def targets():
    for instructor in (False, True):
        edition = "instructor" if instructor else "student"
        yield f"complete-{edition}-course-v1.zip", list(range(1, 17)), instructor
        for chapter in range(1, 17):
            yield (
                f"ch{chapter:02d}/ch{chapter:02d}-{edition}-pack-v1.zip",
                [chapter],
                instructor,
            )


def package():
    records = []
    for name, chapters, instructor in targets():
        expected = members(chapters, instructor)
        path = EDITION / name
        with ZipFile(path, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
            for member, data in sorted(expected.items()):
                info = ZipInfo(member, date_time=(2026, 9, 9, 0, 0, 0))
                info.compress_type = ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                archive.writestr(info, data, compresslevel=9)
        records.append(
            {
                "path": name,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "bytes": path.stat().st_size,
                "members": {
                    member: hashlib.sha256(data).hexdigest()
                    for member, data in sorted(expected.items())
                },
            }
        )
    MANIFEST.write_text(json.dumps({"schemaVersion": 1, "archives": records}, indent=2) + "\n")
    verify()


def verify():
    receipt = json.loads(MANIFEST.read_text())
    records = {row["path"]: row for row in receipt["archives"]}
    assert len(records) == len(receipt["archives"]) == 34
    assert set(records) == {name for name, _, _ in targets()}
    for name, chapters, instructor in targets():
        path = EDITION / name
        row = records[name]
        assert row["bytes"] == path.stat().st_size
        assert row["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
        expected = members(chapters, instructor)
        assert row["members"] == {
            member: hashlib.sha256(data).hexdigest() for member, data in expected.items()
        }
        with ZipFile(path) as archive:
            assert archive.testzip() is None
            assert len(archive.namelist()) == len(expected)
            assert set(archive.namelist()) == set(expected)
            for member, data in expected.items():
                assert archive.read(member) == data
                if not instructor and member.endswith(".ipynb"):
                    notebook = json.loads(data)
                    assert not notebook["metadata"]["course"]["instructor"]
                    assert all(
                        "instructor-check" not in cell.get("metadata", {}).get("tags", [])
                        for cell in notebook["cells"]
                    )
    for index in [EDITION / "START-HERE.md", *EDITION.glob("ch*/README.md")]:
        for destination in re.findall(r"\]\(([^)]+)\)", index.read_text()):
            if not destination.startswith("http"):
                assert (index.parent / destination).is_file(), (index, destination)
    for name, _, _ in targets():
        with ZipFile(EDITION / name) as archive:
            for destination in re.findall(r"\]\(([^)]+)\)", archive.read("START-HERE.md").decode()):
                assert destination in archive.namelist(), (name, destination)
    print("PRACTICAL ARCHIVES: 34 ZIPs; membership, integrity, bytes and index links verified.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    verify() if args.verify else package()
