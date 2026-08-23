"""Low-cardinality fleet metrics. Identifiers belong in evidence, not labels."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class FleetMetrics:
    workers_admitted: int = 0
    workers_expired: int = 0
    workers_draining: int = 0
    lease_age_s_max: float = 0.0
    queue_depth: int = 0
    reservations_held: int = 0
    capacity_cpu: float = 0.0
    refusals: int = 0
    policy_failures: int = 0
    transfers_bytes: int = 0
    reconciliations: int = 0
    unknown_observations: int = 0
    duplicate_finalizations_blocked: int = 0

    def snapshot(self) -> dict[str, Any]:
        return {
            "workers_admitted": self.workers_admitted,
            "workers_expired": self.workers_expired,
            "workers_draining": self.workers_draining,
            "lease_age_s_max": self.lease_age_s_max,
            "queue_depth": self.queue_depth,
            "reservations_held": self.reservations_held,
            "capacity_cpu": self.capacity_cpu,
            "refusals": self.refusals,
            "policy_failures": self.policy_failures,
            "transfers_bytes": self.transfers_bytes,
            "reconciliations": self.reconciliations,
            "unknown_observations": self.unknown_observations,
            "duplicate_finalizations_blocked": self.duplicate_finalizations_blocked,
        }


FleetMetrics = FleetMetrics
