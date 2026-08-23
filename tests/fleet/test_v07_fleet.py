"""v0.7 fleet: protocol, placement, quotas, workers, secrets, artifacts, reconcile."""

from __future__ import annotations

from pathlib import Path

import pytest

from sovereign_agent.artifacts import ArtifactError, ArtifactStore, RemoteWorktree
from sovereign_agent.contracts.execution import NetworkPolicy, SandboxMinimum
from sovereign_agent.contracts.ids import ExecutionId
from sovereign_agent.fleet.coordinator import FleetCoordinator
from sovereign_agent.fleet.network import NetworkGuard
from sovereign_agent.fleet.placement import PlacementEngine, PlacementRefusal
from sovereign_agent.fleet.protocol import (
    ProtocolError,
    ProtocolSession,
    WorkerIdentity,
    WorkerLease,
    decode_frame,
    encode_frame,
)
from sovereign_agent.fleet.reconciliation import (
    ExecutionObservation,
    Observation,
    ReconciliationEngine,
    RetrySafety,
    UnknownState,
)
from sovereign_agent.fleet.registry import WorkerRecord
from sovereign_agent.fleet.reservations import QuotaExceeded, ReservationLedger, ResourceVector
from sovereign_agent.orchestrator.lifecycle import InvocationSpec, WorkerRequest
from sovereign_agent.orchestrator.worker import DockerWorker, IsolationUnavailable, PodmanWorker
from sovereign_agent.secrets import SecretBroker, SecretError
from sovereign_agent.workers import FaultWorker, ScriptedEngine, SshWorker


def _identity(worker_id: str = "w1", backend: str = "docker") -> WorkerIdentity:
    return WorkerIdentity(
        worker_id=worker_id,
        process_instance="proc-1",
        host="host-a",
        backend=backend,
        package_version="0.7.0",
    )


def _enforced_manifest() -> dict:
    def assertion() -> dict:
        return {"available": True, "evidence_level": "enforced", "details": {}}

    return {
        "capabilities": {
            "process_isolation": assertion(),
            "filesystem_isolation": assertion(),
            "network_isolation": assertion(),
            "available": assertion(),
        },
        "network": {"mechanism": "network=none"},
        "platforms": ["host-a"],
    }


def test_protocol_sequences_and_rejects_gaps() -> None:
    identity = _identity()
    session = ProtocolSession(identity, now_s=0)
    first = {"kind": "heartbeat", "worker_id": "w1", "seq": 0}
    ack = session.observe(first)
    assert ack.last_ok_seq == 0
    with pytest.raises(ProtocolError):
        session.observe({"kind": "heartbeat", "worker_id": "w1", "seq": 2})
    session.resume_from(0)
    session.observe({"kind": "heartbeat", "worker_id": "w1", "seq": 1})
    raw = encode_frame(first)
    decoded, rest = decode_frame(raw)
    assert decoded["kind"] == "heartbeat" and rest == b""


def test_stale_fencing_cannot_finalize() -> None:
    identity = _identity()
    session = ProtocolSession(identity, now_s=0)
    lease = WorkerLease(
        lease_id="l1",
        execution_id="e1",
        worker_id="w1",
        fencing=identity.fencing,
        expires_at_s=10,
    )
    stale = {
        "kind": "completion",
        "channel": "canonical",
        "worker_id": "w1",
        "seq": 0,
        "lease": {**lease.to_dict(), "fencing": {"generation": 1, "nonce": "deadbeef"}},
    }
    with pytest.raises(ProtocolError):
        session.require_canonical(stale, lease)
    session.mark_expired()
    session.require_canonical({**stale, "channel": "quarantine", "lease": lease.to_dict()}, lease)


def test_placement_fails_closed_without_enforced_evidence() -> None:
    engine = PlacementEngine()
    worker = WorkerRecord(identity=_identity(), manifest={"capabilities": {}}, admitted=True)
    constraints = {
        "sandbox_minimum": SandboxMinimum.FILESYSTEM_ISOLATED.value,
        "network": NetworkPolicy.DENIED.value,
    }
    with pytest.raises(PlacementRefusal):
        engine.place(requirements={}, effects={}, constraints=constraints, workers=[worker])
    worker.manifest = _enforced_manifest()
    decision = engine.place(requirements={}, effects={}, constraints=constraints, workers=[worker])
    assert decision.worker_id == "w1"


def test_reservations_are_atomic_and_idempotent(tmp_path: Path) -> None:
    ledger = ReservationLedger(
        tmp_path,
        limit=ResourceVector(
            cpu=2,
            memory_bytes=100,
            disk_bytes=10,
            pids=10,
            wall_time_s=10,
            concurrency=2,
            tokens=10,
        ),
    )
    first = ledger.reserve(
        "r1",
        "e1",
        ResourceVector(
            cpu=1, memory_bytes=10, disk_bytes=1, pids=1, wall_time_s=1, concurrency=1, tokens=1
        ),
    )
    again = ledger.reserve(
        "r1",
        "e1",
        ResourceVector(
            cpu=1, memory_bytes=10, disk_bytes=1, pids=1, wall_time_s=1, concurrency=1, tokens=1
        ),
    )
    assert first.reservation_id == again.reservation_id
    with pytest.raises(QuotaExceeded):
        ledger.reserve(
            "r2",
            "e2",
            ResourceVector(
                cpu=2, memory_bytes=10, disk_bytes=1, pids=1, wall_time_s=1, concurrency=1, tokens=1
            ),
        )
    ledger.release("r1")
    ledger.release("r1")
    ledger.reserve(
        "r2",
        "e2",
        ResourceVector(
            cpu=2, memory_bytes=10, disk_bytes=1, pids=1, wall_time_s=1, concurrency=1, tokens=1
        ),
    )


@pytest.mark.asyncio
async def test_docker_and_podman_share_scripted_conformance() -> None:
    engine = ScriptedEngine(name="docker", present=True)
    docker = DockerWorker(engine=engine, image_digest="sha256:" + "ab" * 32)
    podman = PodmanWorker(
        engine=ScriptedEngine(name="podman", present=True),
        image_digest="sha256:" + "cd" * 32,
    )
    request = WorkerRequest(
        execution_id=ExecutionId("e-docker"), session_id="s", session_dir=Path(".")
    )
    handle = await docker.prepare(request)
    result = await docker.execute(handle, InvocationSpec())
    assert result.returncode == 0
    argv = engine.calls[0]["argv"]
    assert "--read-only" in argv
    assert "no-new-privileges" in argv
    assert "ALL" in argv
    assert not any("docker.sock" in str(item) for item in argv)
    await podman.prepare(request)
    await podman.execute(await podman.prepare(request), InvocationSpec())
    assert "--userns=keep-id" in podman._impl.engine.calls[0]["argv"]


@pytest.mark.asyncio
async def test_ssh_refuses_tofu() -> None:
    worker = SshWorker(
        host="example.test",
        user="sa",
        identity_file=Path("/no/key"),
        known_hosts=Path("/no/known_hosts"),
    )
    request = WorkerRequest(
        execution_id=ExecutionId("e-ssh"), session_id="s", session_dir=Path(".")
    )
    with pytest.raises(IsolationUnavailable):
        await worker.prepare(request)


def test_secret_broker_injects_only_at_spawn_and_revokes() -> None:
    broker = SecretBroker({"env": {"TOKEN": "s3cret"}})
    lease = broker.issue("e1", {"TOKEN": "env:TOKEN"}, ttl_s=60)
    assert broker.inject(lease.lease_id) == {"TOKEN": "s3cret"}
    broker.revoke(lease.lease_id)
    with pytest.raises(SecretError):
        broker.inject(lease.lease_id)


def test_network_guard_refuses_unenforced_unknown() -> None:
    guard = NetworkGuard()
    with pytest.raises(PermissionError):
        guard.enforce(NetworkPolicy.UNKNOWN, backend="docker")
    denied = guard.enforce(NetworkPolicy.DENIED, backend="docker")
    assert "none" in denied.mechanism
    restricted = guard.enforce(
        NetworkPolicy.RESTRICTED, backend="docker", allowlist=("example.test:443",)
    )
    assert "example.test:443" in restricted.evidence


def test_artifacts_verify_digest_and_forbid_self_merge(tmp_path: Path) -> None:
    store = ArtifactStore(tmp_path / "cas")
    record = store.put(b"hello", media_type="text/plain", producer_lease="lease-1")
    assert (
        record.digest
        == store.put(
            b"hello",
            media_type="text/plain",
            producer_lease="lease-1",
            expected_digest=record.digest,
        ).digest
    )
    with pytest.raises(ArtifactError):
        store.put(
            b"hello",
            media_type="text/plain",
            producer_lease="lease-1",
            expected_digest="00" * 32,
        )
    tree = RemoteWorktree(tmp_path / "wt", execution_id="e1", base="abc")
    assert tree.prove_commit("abcdef1")["exists"]
    with pytest.raises(ArtifactError):
        tree.merge_self()


def test_reconciliation_quarantines_duplicates_and_unknown() -> None:
    engine = ReconciliationEngine()
    first = ExecutionObservation(
        execution_id="e1",
        desired="completed",
        observed=Observation.COMPLETED,
        retry_safety=RetrySafety.SAFE,
        fencing_generation=2,
        completion_payload={"ok": True},
    )
    assert engine.observe(first).canonical_status == "completed"
    assert engine.observe(first).quarantined is True
    unknown = engine.observe(
        ExecutionObservation(
            execution_id="e2",
            desired="running",
            observed=Observation.UNKNOWN,
            retry_safety=RetrySafety.DECLARED_UNKNOWN,
            fencing_generation=1,
        )
    )
    assert unknown.canonical_status == "unknown"
    with pytest.raises(UnknownState):
        engine.reassign(
            ExecutionObservation(
                execution_id="e2",
                desired="running",
                observed=Observation.UNKNOWN,
                retry_safety=RetrySafety.SAFE,
                fencing_generation=1,
            ),
            fenced=True,
            side_effects_proven_safe=True,
        )


def test_coordinator_blocks_duplicate_finalization(tmp_path: Path) -> None:
    coord = FleetCoordinator(tmp_path)
    identity = _identity()
    coord.register_worker(identity, _enforced_manifest())
    coord.admit_worker("w1")
    dispatch = coord.dispatch(
        execution_id="e1",
        catalog_digest="aa" * 32,
        requirements={},
        effects={},
        constraints={
            "sandbox_minimum": SandboxMinimum.FILESYSTEM_ISOLATED.value,
            "network": NetworkPolicy.DENIED.value,
        },
        resources=ResourceVector(
            cpu=1,
            memory_bytes=1,
            disk_bytes=1,
            pids=1,
            wall_time_s=1,
            concurrency=1,
            tokens=1,
        ),
        invocation={},
    )
    payload = {
        "kind": "completion",
        "channel": "canonical",
        "worker_id": "w1",
        "seq": 0,
        "lease": dispatch.lease.to_dict(),
        "fencing": identity.fencing.to_dict(),
    }
    first = coord.accept_worker_message(payload)
    second = coord.accept_worker_message({**payload, "seq": 1})
    assert first["quarantined"] is False
    assert second["quarantined"] is True
    assert coord.metrics.duplicate_finalizations_blocked == 1


@pytest.mark.asyncio
async def test_fault_worker_cannot_exfiltrate_or_escape() -> None:
    request = WorkerRequest(
        execution_id=ExecutionId("e-fault"), session_id="s", session_dir=Path(".")
    )
    leak = FaultWorker(mode="secret-leak")
    result = await leak.execute(await leak.prepare(request))
    assert "AWS_SECRET_ACCESS_KEY" in result.stdout
    escape = FaultWorker(mode="network-escape")
    with pytest.raises(IsolationUnavailable):
        await escape.execute(await escape.prepare(request))
