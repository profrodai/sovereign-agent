"""Executable pilot-start and proof-pack honesty model."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from pathlib import Path
from typing import Any

STUDENT_TODO = False

SUCCESS_WORDS = re.compile(r"\b(pass(?:ed)?|succeed(?:ed)?|verified live)\b", re.IGNORECASE)
ALLOWED_STATUSES = {"NOT_RUN", "NOT_RUN_UNAVAILABLE", "NOT_RUN_UNAUTHENTICATED", "PASS", "FAIL"}


class PilotStart:
    def __init__(
        self,
        pilot_id: str,
        store_org_id: str,
        pilot_profile_id: str,
        evidence_namespace: str,
    ) -> None:
        self.pilot_id = pilot_id
        self.store_org_id = store_org_id
        self.pilot_profile_id = pilot_profile_id
        self.evidence_namespace = evidence_namespace


def initialize(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    try:
        connection.executescript(
            """
            PRAGMA journal_mode = WAL;
            CREATE TABLE IF NOT EXISTS pilots (
                pilot_id TEXT PRIMARY KEY,
                store_org_id TEXT NOT NULL,
                pilot_profile_id TEXT NOT NULL,
                evidence_namespace TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS active_pilot (
                singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                pilot_id TEXT NOT NULL UNIQUE REFERENCES pilots(pilot_id)
            );
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL,
                subject TEXT NOT NULL
            );
            """
        )
        connection.commit()
    finally:
        connection.close()


def start_pilot(db_path: Path, request: PilotStart, *, fault: str | None = None) -> str:
    connection = sqlite3.connect(db_path, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("BEGIN IMMEDIATE")
        existing = connection.execute(
            "SELECT store_org_id, pilot_profile_id, evidence_namespace "
            "FROM pilots WHERE pilot_id = ?",
            (request.pilot_id,),
        ).fetchone()
        identity = (
            request.store_org_id,
            request.pilot_profile_id,
            request.evidence_namespace,
        )
        if existing is not None:
            if tuple(existing) != identity:
                raise ValueError("pilot_identity_conflict")
            connection.commit()
            return "replay"

        connection.execute(
            "INSERT INTO pilots VALUES (?, ?, ?, ?)",
            (request.pilot_id, *identity),
        )
        if fault == "after_pilot":
            raise RuntimeError("injected_after_pilot")
        try:
            connection.execute(
                "INSERT INTO active_pilot(singleton, pilot_id) VALUES (1, ?)",
                (request.pilot_id,),
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError("pilot_already_active") from exc
        connection.execute(
            "INSERT INTO events(kind, subject) VALUES ('pilot.started', ?)",
            (request.pilot_id,),
        )
        connection.commit()
        return "started"
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()


def pilot_snapshot(db_path: Path) -> dict[str, object]:
    connection = sqlite3.connect(db_path)
    try:
        pilots = connection.execute("SELECT pilot_id FROM pilots ORDER BY pilot_id").fetchall()
        active = connection.execute("SELECT pilot_id FROM active_pilot").fetchone()
        events = connection.execute(
            "SELECT COUNT(*) FROM events WHERE kind = 'pilot.started'"
        ).fetchone()[0]
        return {
            "pilots": [row[0] for row in pilots],
            "active": None if active is None else active[0],
            "started_events": events,
        }
    finally:
        connection.close()


def verify_manifest(manifest: dict[str, Any], evidence_root: Path) -> list[str]:
    """Check internal consistency; deliberately make no authenticity claim."""
    failures: list[str] = []
    status = manifest.get("evaluation", {}).get("status")
    note = manifest.get("evaluation", {}).get("note", "")
    if status not in ALLOWED_STATUSES:
        failures.append("unknown_status")
    if isinstance(status, str) and status.startswith("NOT_RUN") and SUCCESS_WORDS.search(str(note)):
        failures.append("not_run_success_claim")

    root = evidence_root.resolve()
    for artifact in manifest.get("artifacts", []):
        relative = artifact.get("path")
        if not isinstance(relative, str):
            failures.append("invalid_path")
            continue
        candidate = (root / relative).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            failures.append("path_escape")
            continue
        if not candidate.is_file():
            failures.append("missing_artifact")
            continue
        actual = hashlib.sha256(candidate.read_bytes()).hexdigest()
        if actual != artifact.get("sha256"):
            failures.append("digest_mismatch")
    return sorted(set(failures))


def exercise(root: Path) -> dict[str, object]:
    root.mkdir(parents=True, exist_ok=True)
    db_path = root / "pilot.sqlite3"
    initialize(db_path)
    pilot = PilotStart("pilot-lucy-01", "store-lucy", "profile-safe", "evidence/lucy-01")
    start_pilot(db_path, pilot)
    replay = start_pilot(db_path, pilot)

    before_fault = pilot_snapshot(db_path)
    fault = "not_tested"
    try:
        start_pilot(
            db_path,
            PilotStart("pilot-orphan", "store-other", "profile-other", "evidence/other"),
            fault="after_pilot",
        )
    except RuntimeError as exc:
        fault = str(exc)

    evidence = root / "evidence" / "result.txt"
    evidence.parent.mkdir(parents=True, exist_ok=True)
    if not evidence.exists():
        evidence.write_text("local preflight complete\n", encoding="utf-8")
    digest = hashlib.sha256(evidence.read_bytes()).hexdigest()
    valid = {
        "evaluation": {
            "status": "NOT_RUN_UNAUTHENTICATED",
            "note": "Credentialed evaluation did not run.",
        },
        "artifacts": [{"path": "evidence/result.txt", "sha256": digest}],
    }
    attacks = {
        "path_escape": json.loads(json.dumps(valid)),
        "digest_mismatch": json.loads(json.dumps(valid)),
        "not_run_lie": json.loads(json.dumps(valid)),
    }
    attacks["path_escape"]["artifacts"][0]["path"] = "../outside.txt"
    attacks["digest_mismatch"]["artifacts"][0]["sha256"] = "0" * 64
    attacks["not_run_lie"]["evaluation"]["note"] = "Live evaluation passed."

    return {
        "pilot": pilot_snapshot(db_path),
        "replay": replay,
        "fault": fault,
        "no_orphan_after_fault": before_fault == pilot_snapshot(db_path),
        "proof_pack": {
            "valid_failures": verify_manifest(valid, root),
            "attacks": {
                name: verify_manifest(manifest, root) for name, manifest in attacks.items()
            },
            "internally_consistent": True,
            "authenticated": False,
        },
    }
