"""Filesystem-backed durable relay with ordered fenced claims."""

from __future__ import annotations

import hashlib
import json
import os
import random
import secrets
import threading
from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sovereign_agent._internal.atomic import (
    atomic_append_jsonl,
    atomic_write_bytes,
    fsync_directory,
)
from sovereign_agent._internal.file_lock import exclusive_file_lock
from sovereign_agent._internal.hashed import digest
from sovereign_agent.contracts._core import canonical_json_bytes
from sovereign_agent.contracts.ids import RelayMessageId
from sovereign_agent.contracts.redaction import redact_text
from sovereign_agent.registry import RuntimeAddress, SeatInstanceNotFound, SeatRegistry
from sovereign_agent.runtime import RuntimeRoot

from .errors import (
    DuplicateMessageConflict,
    LeaseLost,
    MessageNotFound,
    RelayAuthenticationError,
    RelayCorruptionError,
    RelayValidationError,
)
from .models import (
    Acknowledgement,
    ClaimedMessage,
    DeliveryRecord,
    DeliveryStatus,
    RelayMessage,
)

Clock = Callable[[], datetime]
Notifier = Callable[[RuntimeAddress], None]


class DurableRelay:
    """A local, durable message relay. Notification never affects correctness."""

    def __init__(
        self,
        runtime_root: RuntimeRoot,
        registry: SeatRegistry,
        *,
        clock: Clock | None = None,
        max_attempts: int = 5,
        backoff_base: float = 1.0,
        backoff_cap: float = 300.0,
        notifier: Notifier | None = None,
    ) -> None:
        if max_attempts <= 0 or backoff_base < 0 or backoff_cap < 0:
            raise RelayValidationError("invalid retry policy")
        self.runtime_root = runtime_root.initialize()
        self.registry = registry
        self._clock = clock or (lambda: datetime.now(UTC))
        self.max_attempts = max_attempts
        self.backoff_base = backoff_base
        self.backoff_cap = backoff_cap
        self._notifier = notifier
        self._condition = threading.Condition()
        self._fault_hook = None
        self._legacy_messages = self.runtime_root.relay_dir / "messages"
        self._acks = self.runtime_root.relay_dir / "acknowledgements"
        self._quarantine = self.runtime_root.relay_dir / "quarantine"
        self._attempts = self.runtime_root.relay_dir / "attempts"
        self._conversations = self.runtime_root.relay_dir / "conversations"
        self._state_roots = {
            DeliveryStatus.PENDING: self.runtime_root.relay_dir / "inbox",
            DeliveryStatus.CLAIMED: self.runtime_root.relay_dir / "claimed",
            DeliveryStatus.ACKNOWLEDGED: self.runtime_root.relay_dir / "acknowledged",
            DeliveryStatus.DEAD_LETTERED: self.runtime_root.relay_dir / "dead-letter",
        }
        self._outbox = self.runtime_root.relay_dir / "outbox"
        for directory in (
            *self._state_roots.values(),
            self._outbox,
            self._acks,
            self._quarantine,
            self._attempts,
            self._conversations,
            self._legacy_messages,
        ):
            self._safe_directory(directory)
        self._lock_path = self.runtime_root.locks_dir / "relay.lock"
        self._ensure_regular_or_missing(self._lock_path)
        self._migrate_legacy_messages()

    def enqueue(self, message: RelayMessage) -> DeliveryRecord:
        self._authenticate(message.sender, "sender")
        self._authenticate(message.recipient, "recipient")
        record = DeliveryRecord(message=message, available_at=message.created_at)
        with self._guard():
            existing_path = self._locate(message.message_id)
            if existing_path is not None:
                existing = self._read(existing_path)
                if canonical_json_bytes(existing.message.to_dict()) != canonical_json_bytes(
                    message.to_dict()
                ):
                    raise DuplicateMessageConflict(message.message_id.value)
                return existing
            path = self._record_path(record)
            self._write(path, record)
        self._wake(message.recipient)
        return record

    def claim(
        self,
        recipient: RuntimeAddress | str,
        *,
        owner: str,
        lease_seconds: float = 30.0,
    ) -> ClaimedMessage | None:
        address = recipient if isinstance(recipient, RuntimeAddress) else RuntimeAddress(recipient)
        self._authenticate(address, "recipient")
        if not owner or lease_seconds <= 0:
            raise RelayValidationError("owner must be non-empty and lease_seconds positive")
        with self._guard():
            now = self._now()
            for path, record in self._ordered_records(address):
                if record.status in {
                    DeliveryStatus.ACKNOWLEDGED,
                    DeliveryStatus.DEAD_LETTERED,
                }:
                    continue
                if self._expired(record, now):
                    self._dead_letter(path, record, now, "message expired")
                    continue
                if record.status is DeliveryStatus.CLAIMED:
                    assert record.lease_expires_at is not None
                    if record.lease_expires_at > now:
                        return None
                    record = self._recover_expired(path, record, now)
                    if record.status is DeliveryStatus.DEAD_LETTERED:
                        continue
                if record.available_at is not None and record.available_at > now:
                    return None
                if record.attempt_count >= self.max_attempts:
                    self._dead_letter(path, record, now, "maximum attempts exhausted")
                    continue
                token = secrets.token_hex(16)
                claimed = replace(
                    record,
                    status=DeliveryStatus.CLAIMED,
                    attempt_count=record.attempt_count + 1,
                    lease_owner=owner,
                    lease_token=token,
                    lease_expires_at=now + timedelta(seconds=lease_seconds),
                    lease_owner_pid=os.getpid(),
                    lease_instance=owner,
                )
                self._write(path, claimed)
                self._log_attempt(claimed, "claimed")
                return ClaimedMessage(claimed, token)
        return None

    def acknowledge(
        self,
        message_id: RelayMessageId | str,
        *,
        owner: str,
        lease_token: str,
    ) -> Acknowledgement:
        mid = message_id if isinstance(message_id, RelayMessageId) else RelayMessageId(message_id)
        with self._guard():
            path = self._message_path(mid)
            record = self._required(path, mid)
            now = self._now()
            self._assert_lease(record, owner, lease_token, now)
            acknowledged = replace(
                record,
                status=DeliveryStatus.ACKNOWLEDGED,
                lease_owner=None,
                lease_token=None,
                lease_expires_at=None,
                acknowledged_at=now,
                acknowledged_by=owner,
                acknowledgement_token=lease_token,
            )
            self._write(path, acknowledged)
            ack = Acknowledgement(
                message_id=mid,
                recipient=record.message.recipient,
                lease_owner=owner,
                lease_token=lease_token,
                acknowledged_at=now,
                attempt_count=record.attempt_count,
            )
            atomic_write_bytes(self._ack_path(mid), canonical_json_bytes(ack.to_dict()))
            fsync_directory(self._acks)
            return ack

    ack = acknowledge

    def negative_acknowledge(
        self,
        message_id: RelayMessageId | str,
        *,
        owner: str,
        lease_token: str,
        error: str,
    ) -> DeliveryRecord:
        mid = message_id if isinstance(message_id, RelayMessageId) else RelayMessageId(message_id)
        if not error:
            raise RelayValidationError("negative acknowledgement requires an error")
        with self._guard():
            path = self._message_path(mid)
            record = self._required(path, mid)
            now = self._now()
            self._assert_lease(record, owner, lease_token, now)
            safe_error = redact_text(error)
            if record.attempt_count >= self.max_attempts:
                updated = self._dead_letter(path, record, now, safe_error)
            else:
                delay = min(
                    self.backoff_cap,
                    self.backoff_base * (2 ** max(0, record.attempt_count - 1)),
                )
                delay *= 0.5 + random.random()
                updated = replace(
                    record,
                    status=DeliveryStatus.PENDING,
                    available_at=now + timedelta(seconds=delay),
                    lease_owner=None,
                    lease_token=None,
                    lease_expires_at=None,
                    lease_owner_pid=None,
                    lease_instance=None,
                    last_error=safe_error,
                )
                self._write(path, updated)
                self._log_attempt(updated, "nack")
        self._wake(updated.message.recipient)
        return updated

    nack = negative_acknowledge

    def get(self, message_id: RelayMessageId | str) -> DeliveryRecord:
        mid = message_id if isinstance(message_id, RelayMessageId) else RelayMessageId(message_id)
        return self._required(self._message_path(mid), mid)

    def dead_letters(self, recipient: RuntimeAddress | str | None = None) -> list[DeliveryRecord]:
        address = (
            None
            if recipient is None
            else recipient
            if isinstance(recipient, RuntimeAddress)
            else RuntimeAddress(recipient)
        )
        with self._guard():
            records = [
                record
                for _, record in self._all_records()
                if record.status is DeliveryStatus.DEAD_LETTERED
                and (address is None or record.message.recipient == address)
            ]
        return sorted(records, key=self._order_key)

    def acknowledgement(self, message_id: RelayMessageId | str) -> Acknowledgement | None:
        mid = message_id if isinstance(message_id, RelayMessageId) else RelayMessageId(message_id)
        path = self._ack_path(mid)
        self._ensure_regular_or_missing(path)
        if not path.exists():
            record = self.get(mid)
            if record.status is not DeliveryStatus.ACKNOWLEDGED:
                return None
            assert record.acknowledged_at is not None
            assert record.acknowledged_by is not None
            assert record.acknowledgement_token is not None
            return Acknowledgement(
                message_id=mid,
                recipient=record.message.recipient,
                lease_owner=record.acknowledged_by,
                lease_token=record.acknowledgement_token,
                acknowledged_at=record.acknowledged_at,
                attempt_count=record.attempt_count,
            )
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise TypeError("acknowledgement record is not an object")
            return Acknowledgement.from_dict(data)
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            raise RelayCorruptionError(f"invalid acknowledgement record: {path}") from exc

    def wait_for_notification(self, timeout: float | None = None) -> None:
        """Optional in-process wake-up only; callers must always re-check durable state."""
        with self._condition:
            self._condition.wait(timeout)

    @staticmethod
    def _expired(record: DeliveryRecord, now: datetime) -> bool:
        expires = record.message.expires_at
        return expires is not None and expires <= now

    def _recover_expired(self, path: Path, record: DeliveryRecord, now: datetime) -> DeliveryRecord:
        if record.attempt_count >= self.max_attempts:
            return self._dead_letter(path, record, now, "lease expired at maximum attempts")
        recovered = replace(
            record,
            status=DeliveryStatus.PENDING,
            available_at=now,
            lease_owner=None,
            lease_token=None,
            lease_expires_at=None,
            lease_owner_pid=None,
            lease_instance=None,
            last_error="lease expired",
        )
        self._write(path, recovered)
        self._log_attempt(recovered, "lease-expired-recovery")
        return recovered

    def _dead_letter(
        self, path: Path, record: DeliveryRecord, now: datetime, error: str
    ) -> DeliveryRecord:
        dead = replace(
            record,
            status=DeliveryStatus.DEAD_LETTERED,
            lease_owner=None,
            lease_token=None,
            lease_expires_at=None,
            lease_owner_pid=None,
            lease_instance=None,
            last_error=error,
            dead_lettered_at=now,
        )
        self._write(path, dead)
        self._log_attempt(dead, "dead-letter")
        return dead

    @staticmethod
    def _assert_lease(record: DeliveryRecord, owner: str, token: str, now: datetime) -> None:
        if (
            record.status is not DeliveryStatus.CLAIMED
            or record.lease_owner != owner
            or record.lease_token != token
            or record.lease_expires_at is None
            or record.lease_expires_at <= now
        ):
            raise LeaseLost("claim is no longer the active fencing generation")

    def _authenticate(self, address: RuntimeAddress, role: str) -> None:
        try:
            self.registry.resolve(address)
        except SeatInstanceNotFound as exc:
            raise RelayAuthenticationError(
                f"{role} has no matching local registry evidence: {address.value}"
            ) from exc

    def _ordered_records(self, recipient: RuntimeAddress) -> list[tuple[Path, DeliveryRecord]]:
        return sorted(
            (
                (path, record)
                for path, record in self._all_records()
                if record.message.recipient == recipient
            ),
            key=lambda item: self._order_key(item[1]),
        )

    def inspect_conversation(self, conversation_id: str) -> dict[str, object]:
        path = self._hashed_path(self._conversations, conversation_id)
        if not path.exists():
            return {"conversation_id": conversation_id, "message_ids": []}
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise RelayCorruptionError("conversation index is not an object")
        return data

    def _migrate_legacy_messages(self) -> None:
        for path in sorted(self._legacy_messages.glob("*.json")):
            try:
                record = self._read(path)
            except RelayCorruptionError:
                continue
            target = self._record_path(record)
            if target.resolve() != path.resolve():
                self._write(path, record)

    def _log_attempt(self, record: DeliveryRecord, event: str) -> None:
        path = (
            self.runtime_root.relay_dir
            / "attempts"
            / f"{digest(record.message.message_id.value)}.jsonl"
        )
        atomic_append_jsonl(
            path,
            {
                "event": event,
                "message_id": record.message.message_id.value,
                "status": record.status.value,
                "attempt_count": record.attempt_count,
                "lease_owner": record.lease_owner,
                "lease_owner_pid": record.lease_owner_pid,
            },
        )

    def _index_conversation(self, message: RelayMessage) -> None:
        if not message.conversation_id:
            return
        path = self._hashed_path(self._conversations, message.conversation_id)
        current: dict[str, object] = {"conversation_id": message.conversation_id, "message_ids": []}
        if path.exists():
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                current = loaded
        ids_obj = current.get("message_ids") or []
        ids = [str(item) for item in ids_obj] if isinstance(ids_obj, list) else []
        if message.message_id.value not in ids:
            ids.append(message.message_id.value)
        current["message_ids"] = ids
        atomic_write_bytes(path, canonical_json_bytes(current))

    def _all_records(self) -> list[tuple[Path, DeliveryRecord]]:
        result: list[tuple[Path, DeliveryRecord]] = []
        seen: set[str] = set()
        roots = [
            self._state_roots[DeliveryStatus.CLAIMED],
            self._state_roots[DeliveryStatus.PENDING],
            self._state_roots[DeliveryStatus.ACKNOWLEDGED],
            self._state_roots[DeliveryStatus.DEAD_LETTERED],
            self._outbox,
            self._legacy_messages,
        ]
        for root in roots:
            paths = [root] if root == self._legacy_messages else list(root.glob("*"))
            for directory in paths:
                search = directory if directory.is_dir() else root
                for path in sorted(search.glob("*.json")):
                    try:
                        record = self._read(path)
                    except RelayCorruptionError as exc:
                        quarantine = self._quarantine / f"{path.stem}-{secrets.token_hex(4)}.json"
                        path.replace(quarantine)
                        fsync_directory(path.parent)
                        fsync_directory(self._quarantine)
                        raise RelayCorruptionError(f"record quarantined at {quarantine}") from exc
                    mid = record.message.message_id.value
                    if mid in seen:
                        continue
                    seen.add(mid)
                    result.append((path, record))
        return result

    def _record_dir(self, record: DeliveryRecord) -> Path:
        if record.status is DeliveryStatus.ACKNOWLEDGED and record.message.sender.instance_id:
            # inbound ack lives under acknowledged/<recipient>
            root = self._state_roots[record.status]
        else:
            root = self._state_roots.get(record.status, self._state_roots[DeliveryStatus.PENDING])
        instance = digest(record.message.recipient.instance_id.value)
        return self._safe_directory(root / instance)

    def _record_path(self, record: DeliveryRecord) -> Path:
        return self._hashed_path(self._record_dir(record), record.message.message_id.value)

    def _locate(self, message_id: RelayMessageId) -> Path | None:
        for _, record in self._all_records():
            if record.message.message_id == message_id:
                # _all_records already has path as first of tuples - inefficient.
                break
        for path, record in self._all_records():
            if record.message.message_id == message_id:
                return path
        return None

    def _required(self, path: Path | None, mid: RelayMessageId) -> DeliveryRecord:
        located = path if path is not None and path.exists() else self._locate(mid)
        if located is None:
            raise MessageNotFound(mid.value)
        record = self._read(located)
        if record.message.message_id != mid:
            raise RelayCorruptionError("message filename and envelope identity disagree")
        return record

    def _write(self, old_path: Path, record: DeliveryRecord) -> None:
        target = self._record_path(record)
        self._ensure_regular_or_missing(target)
        atomic_write_bytes(target, canonical_json_bytes(record.to_dict()))
        fsync_directory(target.parent)
        if old_path.resolve() != target.resolve() and old_path.exists():
            old_path.unlink()
            fsync_directory(old_path.parent)
        if self._fault_hook is not None:
            self._fault_hook(record.status.value, target)
        if record.message.conversation_id:
            self._index_conversation(record.message)
        if record.status is DeliveryStatus.PENDING:
            outbox = self._hashed_path(
                self._safe_directory(
                    self._outbox / digest(record.message.sender.instance_id.value)
                ),
                record.message.message_id.value,
            )
            if not outbox.exists():
                atomic_write_bytes(outbox, canonical_json_bytes(record.to_dict()))

    def _message_path(self, message_id: RelayMessageId) -> Path:
        located = self._locate(message_id)
        if located is not None:
            return located
        dummy_recipient = "unknown"
        return self._hashed_path(
            self._safe_directory(
                self._state_roots[DeliveryStatus.PENDING] / digest(dummy_recipient)
            ),
            message_id.value,
        )

    def _ack_path(self, message_id: RelayMessageId) -> Path:
        return self._hashed_path(self._acks, message_id.value)

    def _hashed_path(self, parent: Path, value: str) -> Path:
        path = self.runtime_root.path(
            parent.relative_to(self.runtime_root.root)
            / f"{hashlib.sha256(value.encode()).hexdigest()}.json"
        )
        if path.parent != parent.resolve():
            raise RelayValidationError("relay record escaped its directory")
        return path

    def _safe_directory(self, path: Path) -> Path:
        if path.is_symlink():
            raise RelayValidationError(f"relay directory must not be a symlink: {path}")
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
        if not path.is_dir():
            raise RelayValidationError(f"relay path is not a directory: {path}")
        path.resolve().relative_to(self.runtime_root.root.resolve())
        return path

    def _read(self, path: Path) -> DeliveryRecord:
        self._ensure_regular_or_missing(path)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise TypeError("record is not an object")
            return DeliveryRecord.from_dict(data)
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            raise RelayCorruptionError(f"invalid relay record: {path}") from exc

    @staticmethod
    def _order_key(record: DeliveryRecord) -> tuple[datetime, str, str]:
        conversation = record.message.conversation_id or ""
        return record.message.created_at, conversation, record.message.message_id.value

    @staticmethod
    def _ensure_regular_or_missing(path: Path) -> None:
        if path.is_symlink():
            raise RelayValidationError(f"relay file must not be a symlink: {path}")
        if path.exists() and not path.is_file():
            raise RelayValidationError(f"relay record must be a regular file: {path}")

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise RelayValidationError("clock must return a timezone-aware datetime")
        return value.astimezone(UTC)

    def _guard(self) -> AbstractContextManager[None]:
        self._ensure_regular_or_missing(self._lock_path)
        return exclusive_file_lock(self._lock_path)

    def _wake(self, recipient: RuntimeAddress) -> None:
        with self._condition:
            self._condition.notify_all()
        if self._notifier is not None:
            self._notifier(recipient)


Relay = DurableRelay

__all__ = ["DurableRelay", "Relay"]
