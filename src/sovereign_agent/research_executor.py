"""One bounded, owned synthetic executor, with identity-based reconciliation.

Files describe the external executor, never agent authority. An exclusive claim
prevents duplicate evaluation; a dead claimed worker holds UNKNOWN, not a retry.
This is not an isolation boundary for arbitrary research code.
"""

from __future__ import annotations

import hashlib
import os
import stat
import subprocess
import sys
import time
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from sovereign_agent.providers.base import allowed_environment
from sovereign_agent.workspace import safe_join


class Request(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)
    operation: str = Field(pattern=r"^[a-f0-9]{32}$")
    x: float = Field(ge=-2, le=2)
    delay: float = Field(default=0.1, ge=0, le=3)


class Receipt(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)
    operation: str
    request_digest: str
    status: Literal["COMPLETED", "CANCELED"]
    x: float
    value: float | None
    cpu_seconds: float = Field(ge=0, le=5)
    wall_seconds: float = Field(ge=0, le=10)
    max_rss: int = Field(ge=0)


def read_paper(source: dict[str, object], locator: str, operation: str) -> dict[str, object]:
    """Closed in-process read of an admitted immutable extraction; no new process."""
    from sovereign_agent import paper_assessment

    return paper_assessment.observe(source, locator, operation)


def digest(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def directory(root: Path, identifier: str) -> Path:
    if len(identifier) != 32 or any(c not in "0123456789abcdef" for c in identifier):
        raise ValueError("invalid operation identity")
    return safe_join(root, ".sovereign/executor/" + identifier)


def submit(root: Path, raw: str) -> None:
    request = Request.model_validate_json(raw)
    folder = directory(root, request.operation)
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = folder / "request.json"
    try:
        with path.open("x") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError:
        if path.read_text() != raw:
            raise ValueError("executor identity reused") from None
    if not (folder / "claimed").exists():
        subprocess.Popen(
            [sys.executable, "-m", __name__, str(folder)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            env=allowed_environment("PATH", "HOME", "USER", "LOGNAME", "LANG", "LC_ALL", "TMPDIR"),
        )


def collect(root: Path, raw: str) -> tuple[Receipt, str] | None:
    request = Request.model_validate_json(raw)
    path = directory(root, request.operation) / "result.json"
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    except FileNotFoundError:
        return None
    except OSError:
        raise ValueError("receipt must be a regular file, not an alias") from None
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > 8192:
            raise ValueError("receipt must be a bounded regular file")
        content = os.read(descriptor, 8193)
    finally:
        os.close(descriptor)
    if len(content) > 8192:
        raise ValueError("oversized executor receipt")
    receipt = Receipt.model_validate_json(content)
    if (
        receipt.operation != request.operation
        or receipt.request_digest != digest(raw)
        or receipt.x != request.x
        or (receipt.status == "COMPLETED") != (receipt.value is not None)
    ):
        raise ValueError("receipt identity or measurement mismatch")
    return receipt, digest(content.decode())


def execute(folder: Path) -> None:
    import resource

    try:
        (folder / "claimed").mkdir()
    except FileExistsError:
        return
    raw = (folder / "request.json").read_text()
    request = Request.model_validate_json(raw)
    wall, cpu = time.monotonic(), time.process_time()
    time.sleep(request.delay)
    canceled = (folder / "cancel").exists()
    # Only this fixed cheap objective is permitted. Replication is deterministic.
    value = None if canceled else (request.x - 0.375) ** 2 + 0.05 * (request.x + 1) ** 2
    receipt = Receipt(
        operation=request.operation,
        request_digest=digest(raw),
        status="CANCELED" if canceled else "COMPLETED",
        x=request.x,
        value=value,
        cpu_seconds=time.process_time() - cpu,
        wall_seconds=time.monotonic() - wall,
        max_rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    )
    temporary = folder / "result.tmp"
    with temporary.open("x") as stream:
        stream.write(receipt.model_dump_json())
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(folder / "result.json")


if __name__ == "__main__":
    execute(Path(sys.argv[1]))
