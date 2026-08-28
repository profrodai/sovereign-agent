"""Actor registry loaded from committed, non-secret TOML."""

from __future__ import annotations

import tomllib
from pathlib import Path

from sovereign_agent.files import dump_toml, write_text
from sovereign_agent.models import Actor, Role

DEFAULT_ACTORS = [
    {
        "id": "principal-human",
        "role": "principal",
        "provider": "human",
        "authority": ["define_outcome", "accept", "grant_exception", "rule"],
    },
    {
        "id": "master-course",
        "role": "master",
        "provider": "scripted",
        "authority": ["plan", "assign", "integrate", "request_ruling"],
    },
    {
        "id": "operator-course",
        "role": "operator",
        "provider": "scripted",
        "authority": ["read", "write_workspace", "run_checks", "report"],
    },
    {
        "id": "sparring-course",
        "role": "sparring",
        "provider": "scripted",
        "authority": ["read", "review", "rule"],
    },
    {
        "id": "verifier-course",
        "role": "verifier",
        "provider": "deterministic",
        "authority": ["run_checks", "record_evidence"],
    },
]


def default_config() -> dict[str, object]:
    return {"schema_version": 1, "actors": DEFAULT_ACTORS}


def write_config(path: Path, config: dict[str, object] | None = None) -> None:
    write_text(path, dump_toml(config or default_config()))


def load_actors(path: Path) -> list[Actor]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    actors = []
    for raw in data.get("actors", []):
        # workspace_policy is genuinely optional: omitted from TOML, the
        # model's own default ("temporary_directory") applies. Passed only
        # when present, rather than always passed with a `.get(..., default)`
        # that would need to duplicate the model's default here too.
        actor = (
            Actor(
                id=raw["id"],
                role=Role(raw["role"]),
                provider=raw["provider"],
                authority=list(raw.get("authority", [])),
                workspace_policy=raw["workspace_policy"],
            )
            if "workspace_policy" in raw
            else Actor(
                id=raw["id"],
                role=Role(raw["role"]),
                provider=raw["provider"],
                authority=list(raw.get("authority", [])),
            )
        )
        actors.append(actor)
    return actors
