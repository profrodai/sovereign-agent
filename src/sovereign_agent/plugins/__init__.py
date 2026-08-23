"""Plugin discovery, allowlisting, compatibility, and isolated lifecycle."""

from __future__ import annotations

import importlib
import importlib.metadata
import threading
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

from sovereign_agent.registries import Registry


class PluginLoadError(RuntimeError):
    pass


@dataclass(frozen=True)
class PluginManifest:
    manifest_version: int
    name: str
    kind: str
    package: str
    package_version: str
    api_range: str
    capabilities: tuple[str, ...]
    isolation_requirement: str = "process"
    required: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PluginManifest:
        return cls(
            manifest_version=int(data.get("manifest_version", 1)),
            name=str(data["name"]),
            kind=str(data["kind"]),
            package=str(data["package"]),
            package_version=str(data.get("package_version", "0")),
            api_range=str(data["api_range"]),
            capabilities=tuple(data.get("capabilities") or ()),
            isolation_requirement=str(data.get("isolation_requirement", "process")),
            required=bool(data.get("required", False)),
        )


def _package_version() -> str:
    from sovereign_agent import __version__

    return __version__


def api_range_compatible(spec: str, version: str | None = None) -> bool:
    """Accept simple '>=X,<Y' ranges without a packaging dependency."""
    if version is None:
        version = _package_version()
    parts = [item.strip() for item in spec.split(",") if item.strip()]
    ver = _parse(version)
    for part in parts:
        if part.startswith(">="):
            if ver < _parse(part[2:]):
                return False
        elif part.startswith("<"):
            if not ver < _parse(part[1:]):
                return False
        else:
            return False
    return True


def _parse(value: str) -> tuple[int, ...]:
    return tuple(int(item) for item in value.split(".") if item.isdigit())


class PluginLoader:
    def __init__(
        self,
        registry: Registry[Any],
        *,
        allowlist: Iterable[str] = (),
        current_api: str | None = None,
        entry_points: Callable[[], Iterable[Any]] | None = None,
        setup_timeout: float = 5.0,
    ) -> None:
        self.registry = registry
        self.allowlist = set(allowlist)
        self.current_api = current_api or _package_version()
        self._entry_points = entry_points or (
            lambda: importlib.metadata.entry_points().select(group="sovereign_agent.plugins")
        )
        self.setup_timeout = setup_timeout
        self.failures: list[str] = []

    def discover(self) -> list[PluginManifest]:
        manifests: list[PluginManifest] = []
        for point in self._entry_points():
            attrs = getattr(point, "attrs", {}) or {}
            name = getattr(point, "name", None) or attrs.get("name")
            if not name:
                continue
            dist = getattr(point, "dist", None)
            package = getattr(dist, "name", None) or attrs.get("package", name)
            version = str(attrs.get("package_version", "0"))
            if dist is not None:
                version = str(getattr(dist, "version", version))
            manifest = PluginManifest.from_dict(
                {
                    "name": name,
                    "kind": attrs.get("kind", "channel"),
                    "package": package,
                    "package_version": version,
                    "api_range": attrs.get("api_range", ">=0.5,<0.6"),
                    "capabilities": attrs.get("capabilities", ()),
                    "required": attrs.get("required", False),
                    "module": getattr(point, "value", ""),
                }
            )
            manifests.append(manifest)
        return manifests

    def load(self) -> list[PluginManifest]:
        loaded: list[PluginManifest] = []
        seen: set[tuple[str, str]] = set()
        for manifest in self.discover():
            key = (manifest.name, manifest.kind)
            if key in seen:
                raise PluginLoadError(f"duplicate plugin {manifest.name!r} kind {manifest.kind!r}")
            seen.add(key)
            if manifest.name not in self.allowlist:
                if manifest.required:
                    raise PluginLoadError(f"required plugin {manifest.name!r} is not allowlisted")
                self.failures.append(f"skipped {manifest.name}: not allowlisted")
                continue
            if not api_range_compatible(manifest.api_range, self.current_api):
                message = f"incompatible plugin {manifest.name}: {manifest.api_range}"
                if manifest.required:
                    raise PluginLoadError(message)
                self.failures.append(message)
                continue
            try:
                self._instantiate(manifest)
                loaded.append(manifest)
            except Exception as exc:  # noqa: BLE001
                message = f"plugin {manifest.name} failed: {exc}"
                if manifest.required:
                    raise PluginLoadError(message) from exc
                self.failures.append(message)
        return loaded

    def _instantiate(self, manifest: PluginManifest) -> None:
        for point in self._entry_points():
            if getattr(point, "name", None) != manifest.name:
                continue
            current_point = point
            errors: list[BaseException] = []

            def target(ep: Any = current_point, bucket: list[BaseException] = errors) -> None:
                try:
                    plugin = ep.load()
                    if callable(plugin) and not hasattr(plugin, "kind"):
                        plugin = plugin()
                    if getattr(plugin, "kind", None) == "governance":
                        raise PluginLoadError("plugins cannot gain governance authority")
                    self.registry.register(plugin)
                except BaseException as exc:  # noqa: BLE001
                    bucket.append(exc)

            worker = threading.Thread(target=target, daemon=True)
            worker.start()
            worker.join(self.setup_timeout)
            if worker.is_alive():
                raise PluginLoadError(f"plugin {manifest.name} setup timed out")
            if errors:
                raise errors[0]
            return
        raise PluginLoadError(f"entry point missing for {manifest.name}")
