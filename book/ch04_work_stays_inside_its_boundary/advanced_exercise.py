"""Chapter 4 extension: test five isolation planes without saying 'sandbox'."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sovereign_agent.errors import Refusal
from sovereign_agent.isolation import IsolationPolicy


def explore_isolation(root: Path) -> dict[str, object]:
    root = root.resolve()
    workspace = (root / "workspace").resolve()
    outside = (root / "outside").resolve()
    workspace.mkdir(parents=True)
    outside.mkdir()
    (workspace / "escape").symlink_to(outside, target_is_directory=True)
    policy = IsolationPolicy(
        filesystem_roots=(workspace,),
        network_hosts=frozenset({"inventory.example.test"}),
        credential_names=frozenset({"INVENTORY_TOKEN"}),
        allowed_tools=frozenset({"read_inventory", "shell"}),
        denied_tools=frozenset({"shell"}),
    )

    refusals: dict[str, str] = {}
    for name, operation in (
        ("symlink_escape", lambda: policy.authorize_path(workspace / "escape" / "proof.txt")),
        ("unlisted_host", lambda: policy.authorize_network("payments.example.test")),
        ("denied_tool", lambda: policy.authorize_tool("shell")),
    ):
        try:
            operation()
            refusals[name] = "ALLOWED (this would be a bug)"
        except Refusal:
            refusals[name] = "REFUSED"

    return {
        "allowed_path": str(policy.authorize_path(workspace / "receipt.json").relative_to(root)),
        "allowed_host": policy.authorize_network("INVENTORY.EXAMPLE.TEST."),
        "allowed_credential_name": policy.authorize_credential("INVENTORY_TOKEN"),
        "refusals": refusals,
        "plane_verdicts": {item.plane: item.verdict for item in policy.explain()},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    print(json.dumps(explore_isolation(parser.parse_args().root), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
