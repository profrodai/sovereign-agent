"""Session filesystem operations authored as ZeoCore capabilities, owned by Sovereign."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field
from zeo_core.contracts import (
    CapabilityExample,
    CapabilityRequirements,
    CapabilityResult,
    ConcurrencyMode,
    EffectKind,
    FilesystemRequirement,
)
from zeo_core.tools import BoundCapability, ToolContext, bound_capability_of, capability

from sovereign_agent._internal.atomic import atomic_write_text
from sovereign_agent.errors import IOError as SovereignIOError
from sovereign_agent.session.directory import Session


class SessionFilesystem:
    """Scoped workspace access. Not the full Session object."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def resolve(self, path: str) -> Path:
        return self._session.path(f"workspace/{path}")


class ReadFileRequest(BaseModel):
    path: str


class ReadFileResponse(BaseModel):
    path: str
    content: str
    size_bytes: int


class WriteFileRequest(BaseModel):
    path: str
    content: str


class WriteFileResponse(BaseModel):
    path: str
    bytes_written: int


class ListFilesRequest(BaseModel):
    path: str = "."


class ListFilesResponse(BaseModel):
    path: str
    entries: list[dict] = Field(default_factory=list)


def _fs(ctx: ToolContext) -> SessionFilesystem:
    service = ctx.get_service("session.filesystem")
    if not isinstance(service, SessionFilesystem):
        raise SovereignIOError(
            code="SA_IO_NOT_FOUND",
            message="session filesystem is not in the capability context",
        )
    return service


@capability(
    id="sovereign.session.file.read@1.0.0",
    description="Read a file from the authorized session filesystem.",
    effects={EffectKind.READ},
    concurrency=ConcurrencyMode.PARALLEL_SAFE,
    requirements=CapabilityRequirements(
        filesystem=FilesystemRequirement(read=True, roles=("workspace",))
    ),
    projection_name="read_file",
    error_codes=("ZEO_IO_NOT_FOUND", "ZEO_IO_SESSION_ESCAPE"),
    examples=(
        CapabilityExample(
            request={"path": "notes.md"},
            response={"path": "notes.md", "content": "...", "size_bytes": 3},
        ),
    ),
)
def read_file(request: ReadFileRequest, ctx: ToolContext) -> CapabilityResult[ReadFileResponse]:
    try:
        resolved = _fs(ctx).resolve(request.path)
        if not resolved.exists():
            return CapabilityResult.fail(
                msg=f"file not found in workspace: {request.path}",
                code="ZEO_IO_NOT_FOUND",
            )
        content = resolved.read_text(encoding="utf-8")
        return CapabilityResult.ok(
            data=ReadFileResponse(
                path=request.path,
                content=content,
                size_bytes=len(content.encode()),
            ),
            msg=f"read {request.path} ({len(content)} chars)",
        )
    except SovereignIOError as exc:
        return CapabilityResult.fail(msg=str(exc), code="ZEO_IO_SESSION_ESCAPE")


@capability(
    id="sovereign.session.file.write@1.0.0",
    description="Write a file to the authorized session filesystem.",
    effects={EffectKind.WRITE},
    concurrency=ConcurrencyMode.SERIAL_PER_RESOURCE,
    resource_key_fields=("path",),
    requirements=CapabilityRequirements(
        filesystem=FilesystemRequirement(read=True, write=True, roles=("workspace",))
    ),
    projection_name="write_file",
    error_codes=("ZEO_IO_SESSION_ESCAPE", "ZEO_IO_ATOMIC_WRITE_FAILED"),
    examples=(
        CapabilityExample(
            request={"path": "report.md", "content": "# Report\n..."},
            response={"path": "report.md", "bytes_written": 10},
        ),
    ),
)
def write_file(request: WriteFileRequest, ctx: ToolContext) -> CapabilityResult[WriteFileResponse]:
    try:
        resolved = _fs(ctx).resolve(request.path)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_text(resolved, request.content)
        return CapabilityResult.ok(
            data=WriteFileResponse(path=request.path, bytes_written=len(request.content.encode())),
            msg=f"wrote {request.path} ({len(request.content)} chars)",
        )
    except SovereignIOError as exc:
        return CapabilityResult.fail(msg=str(exc), code="ZEO_IO_SESSION_ESCAPE")


@capability(
    id="sovereign.session.file.list@1.0.0",
    description="List files in a directory under the authorized session filesystem.",
    effects={EffectKind.READ},
    concurrency=ConcurrencyMode.PARALLEL_SAFE,
    requirements=CapabilityRequirements(
        filesystem=FilesystemRequirement(read=True, roles=("workspace",))
    ),
    projection_name="list_files",
    error_codes=("ZEO_IO_SESSION_ESCAPE",),
    examples=(
        CapabilityExample(
            request={"path": "."},
            response={"path": ".", "entries": []},
        ),
    ),
)
def list_files(request: ListFilesRequest, ctx: ToolContext) -> CapabilityResult[ListFilesResponse]:
    try:
        resolved = _fs(ctx).resolve(request.path)
        if not resolved.exists():
            return CapabilityResult.ok(
                data=ListFilesResponse(path=request.path, entries=[]),
                msg=f"{request.path} has no entries (does not exist)",
            )
        entries = []
        for entry in sorted(resolved.iterdir()):
            entries.append(
                {
                    "name": entry.name,
                    "type": "dir" if entry.is_dir() else "file",
                    "size_bytes": entry.stat().st_size if entry.is_file() else None,
                }
            )
        return CapabilityResult.ok(
            data=ListFilesResponse(path=request.path, entries=entries),
            msg=f"{request.path}: {len(entries)} entries",
        )
    except SovereignIOError as exc:
        return CapabilityResult.fail(msg=str(exc), code="ZEO_IO_SESSION_ESCAPE")


def bind_session_file_capabilities() -> list[BoundCapability]:
    return [
        bound_capability_of(read_file),
        bound_capability_of(write_file),
        bound_capability_of(list_files),
    ]
