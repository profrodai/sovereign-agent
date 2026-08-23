"""Deterministic v0.5 distribution and compatibility verification.

This gate never publishes, contacts a provider, or reads credentials.  It proves
that the declared API and version match the documentation, that the distributions
contain the complete runtime package, and that a core-only wheel works in a clean
environment without import-time filesystem/network/process activity.
"""

from __future__ import annotations

import argparse
import ast
import os
import subprocess
import tarfile
import tempfile
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "src" / "sovereign_agent"
API_V02 = ROOT / "docs" / "public-api-v0.2.txt"
API_V03 = ROOT / "docs" / "public-api-v0.3.txt"
API_V04 = ROOT / "docs" / "public-api-v0.4.txt"
API_V05 = ROOT / "docs" / "public-api-v0.5.txt"
EXPECTED_VERSION = "0.5.0"
REQUIRED_SCHEMAS = {
    "sovereign_agent/contracts/schemas/capability-manifest.schema.json",
    "sovereign_agent/contracts/schemas/execution-receipt.schema.json",
    "sovereign_agent/contracts/schemas/governed-execution-request.schema.json",
}


def _manifest(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]


def _source_exports() -> list[str]:
    tree = ast.parse((PACKAGE / "__init__.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets
        ):
            value = ast.literal_eval(node.value)
            if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                break
            return sorted(value)
    raise AssertionError("sovereign_agent.__all__ must be a literal list of strings")


def _source_runtime_files() -> set[str]:
    return {
        path.relative_to(PACKAGE.parent).as_posix()
        for path in PACKAGE.rglob("*")
        if path.is_file()
        and path.suffix in {".py", ".json", ".toml", ".yaml", ".yml", ".j2", ".tmpl"}
    }


def _distribution_files(path: Path) -> set[str]:
    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as archive:
            return {
                name
                for name in archive.namelist()
                if name.startswith("sovereign_agent/") and not name.endswith("/")
            }
    with tarfile.open(path) as archive:
        names = set()
        for name in archive.getnames():
            marker = "/src/"
            if marker in name:
                relative = name.split(marker, 1)[1]
                if relative.startswith("sovereign_agent/"):
                    names.add(relative)
        return names


def _run(
    *command: str,
    cwd: Path = ROOT,
    env: dict[str, str] | None = None,
    timeout: int = 300,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode:
        detail = (result.stdout + result.stderr).strip()
        raise AssertionError(f"{' '.join(command)} failed ({result.returncode}):\n{detail}")
    return result


def _clean_wheel_smoke(wheel: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="sovereign-agent-release-") as raw:
        temp = Path(raw)
        venv = temp / "venv"
        _run("uv", "venv", "--seed", str(venv))
        python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        _run("uv", "pip", "install", "--python", str(python), str(wheel))

        smoke = temp / "smoke.py"
        smoke.write_text(
            """
import importlib.resources
import json
import os
import pathlib
import socket
import subprocess
import sys

def forbidden(kind):
    def fail(*args, **kwargs):
        raise AssertionError(f"import attempted {kind}")
    return fail

socket.socket.connect = forbidden("network connect")
socket.socket.connect_ex = forbidden("network connect")
socket.socket.bind = forbidden("socket bind")
socket.socket.listen = forbidden("socket listen")
subprocess.Popen = forbidden("process creation")
os.system = forbidden("process creation")

def audit(event, args):
    if event == "open":
        mode = args[1]
        flags = args[2]
        writing = (
            isinstance(mode, str) and any(char in mode for char in "wax+")
        ) or (
            isinstance(flags, int)
            and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
        )
        if writing:
            raise AssertionError(f"import attempted filesystem write: {args[0]}")
    if event in {
        "os.mkdir", "os.rename", "os.remove", "os.rmdir", "os.symlink",
        "socket.connect", "socket.bind", "subprocess.Popen", "os.system",
    }:
        raise AssertionError(f"import attempted side effect: {event}")

sys.addaudithook(audit)
before = sorted(str(p.relative_to(pathlib.Path.cwd())) for p in pathlib.Path.cwd().rglob("*"))
import sovereign_agent as sa
after = sorted(str(p.relative_to(pathlib.Path.cwd())) for p in pathlib.Path.cwd().rglob("*"))
assert before == after, (before, after)
assert sa.__version__ == os.environ["SOVEREIGN_EXPECTED_VERSION"]
assert len(sa.__all__) == len(set(sa.__all__))
schemas = importlib.resources.files("sovereign_agent.contracts.schemas")
for name in (
    "capability-manifest.schema.json",
    "execution-receipt.schema.json",
    "governed-execution-request.schema.json",
):
    json.loads(schemas.joinpath(name).read_text(encoding="utf-8"))
print(json.dumps({"version": sa.__version__, "exports": len(sa.__all__)}))
""".lstrip(),
            encoding="utf-8",
        )
        env = {
            **os.environ,
            "HOME": str(temp / "home"),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONNOUSERSITE": "1",
            "SOVEREIGN_EXPECTED_VERSION": EXPECTED_VERSION,
        }
        (temp / "home").mkdir()
        _run(str(python), "-I", "-B", str(smoke), cwd=temp, env=env)
        _run(
            str(
                venv / ("Scripts/sovereign-agent.exe" if os.name == "nt" else "bin/sovereign-agent")
            ),
            "version",
            cwd=temp,
            env=env,
        )


def verify_source() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert project["version"] == EXPECTED_VERSION

    init_text = (PACKAGE / "__init__.py").read_text(encoding="utf-8")
    assert f'__version__ = "{EXPECTED_VERSION}"' in init_text

    v02 = _manifest(API_V02)
    v03 = _manifest(API_V03)
    v04 = _manifest(API_V04)
    v05 = _manifest(API_V05)
    assert v02 == sorted(v02), "v0.2 API manifest must be sorted"
    assert v03 == sorted(v03), "v0.3 API manifest must be sorted"
    assert v04 == sorted(v04), "v0.4 API manifest must be sorted"
    assert v05 == sorted(v05), "v0.5 API manifest must be sorted"
    assert len(v02) == 67 and len(v02) == len(set(v02))
    assert len(v03) == 152 and len(v03) == len(set(v03))
    assert v03 == v04
    assert len(v05) == 161 and len(v05) == len(set(v05))
    assert set(v02) <= set(v03), "v0.3 removed a stable v0.2 symbol"
    assert set(v04) <= set(v05), "v0.5 removed a stable v0.4 symbol"
    assert _source_exports() == v05, "documented v0.5 API differs from __all__"

    for required in (
        ROOT / "docs" / "migration-v0.2-to-v0.3.md",
        ROOT / "docs" / "migration-v0.3-to-v0.4.md",
        ROOT / "docs" / "migration-v0.4-to-v0.5.md",
        ROOT / "docs" / "threat-model.md",
        ROOT / "docs" / "release-notes" / "0.3.0.md",
        ROOT / "docs" / "release-notes" / "0.4.0.md",
        ROOT / "docs" / "release-notes" / "0.5.0.md",
        ROOT / "docs" / "teaching-surface.md",
        ROOT / "docs" / "v0.4-operator-guide.md",
    ):
        assert required.is_file(), f"missing release document: {required.relative_to(ROOT)}"


def verify_distribution(path: Path) -> None:
    files = _distribution_files(path)
    missing = _source_runtime_files() - files
    assert not missing, f"{path.name} is missing runtime files: {sorted(missing)}"
    assert REQUIRED_SCHEMAS <= files, f"{path.name} is missing required schemas"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheel", type=Path)
    parser.add_argument("--sdist", type=Path)
    args = parser.parse_args()

    verify_source()
    print("✓ version and API manifests agree; all 67 v0.2 exports remain")

    if args.wheel:
        verify_distribution(args.wheel)
        _clean_wheel_smoke(args.wheel.resolve())
        print(f"✓ wheel content, core-only install, CLI, schemas, and import purity: {args.wheel}")
    if args.sdist:
        verify_distribution(args.sdist)
        print(f"✓ sdist contains the complete runtime package: {args.sdist}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
