## Restoring bytes does not restore the outside world

Lucy restores yesterday's database after a disk problem. The supplier may have accepted another
order since that backup. The local database now describes an older state, while the supplier has
not traveled backward. A **backup** is a retained copy under a stated consistency contract.
A **restore** replaces local state from that copy. **Reconciliation** compares restored knowledge
with independent current evidence before work resumes.

A **manifest** lists expected files or records and their identities. An **integrity check** can
detect corrupt bytes. A **schema version** describes the structure the running code expects.
A valid digest does not prove schema compatibility, and schema compatibility does not prove
freshness. Check these questions separately before mutating the live database.

### Observe a missing file and a changed file

The example models a two-file backup manifest. Predict which candidate is intact, which has a
missing member and which contains a changed value. Comparing only the files that happen to be
present would miss the absent authority record.

```python tags=["foundation", "worked-example"]
import hashlib

intro_backup_files = {"database": b"consistent snapshot", "authority": b"era-4"}
intro_manifest = {
    name: hashlib.sha256(value).hexdigest() for name, value in intro_backup_files.items()
}
intro_candidates = [
    dict(intro_backup_files),
    {"database": b"consistent snapshot"},
    {**intro_backup_files, "database": b"corrupt snapshot"},
]
for intro_candidate in intro_candidates:
    intro_observed = {
        name: hashlib.sha256(value).hexdigest() for name, value in intro_candidate.items()
    }
    print("Exact members and bytes:", intro_observed == intro_manifest)
```

This demonstrates comparison logic, not a SQLite backup procedure. Copying a database file at
an arbitrary moment is not interchangeable with using SQLite's backup interface, especially
when journal state matters. The book's supplied `Database` wrapper exposes the actual backup
and restore operations; the construction task works with their real schema and connections.

### Pause before a restored image can admit new work

Pausing the old live connection is insufficient if the snapshot being copied over it contains
an unpaused control row. The prepared restored image itself must carry paused state. It also
gets a fresh authority epoch so surviving workers from before the restore cannot write using
their former claims. Old ownership and approvals are cleared or revoked according to the
chapter's restore contract.

```python tags=["foundation", "worked-example"]
intro_old_live = {"paused": True, "epoch": "current-era"}
intro_backup_control = {"paused": False, "epoch": "old-era"}
intro_naive_restore = dict(intro_backup_control)
intro_prepared_restore = {**intro_backup_control, "paused": True, "epoch": "fresh-era"}
print("Naive copy paused:", intro_naive_restore["paused"])
print("Prepared image paused:", intro_prepared_restore["paused"])
assert intro_prepared_restore["paused"] and not intro_naive_restore["paused"]
```

An **inode** is the filesystem identity of a file on relevant systems. Existing open connections
can keep referring to an old file if a pathname is simply replaced. The actual restore path
uses the database backup mechanism into the existing destination connection and separately
publishes the authority marker. You do not need to implement a filesystem to understand why
path equality and open-handle identity are different questions.

### Prepare, validate, publish, reconcile, resume

The restore builds a temporary prepared image, checks integrity and schema, assigns a fresh
epoch, clears stale ownership and leaves the result paused. The authority marker is published
with the intended durability steps before normal work is allowed to resume. A failed preflight
should preserve the live work. “The command returned” is weaker evidence than observing the
resulting control state and refusing a stale claim.

After restore, compare local orders with the supplier's retained operation identities. A missing
local order may reflect backup age, not supplier failure. Historical model usage may be incomplete;
report that uncertainty rather than reconstructing a confident total from missing rows.

Unit A constructs the real restore function. Unit B removes the prepared-image pause and tries
the normal claim API, exposing unauthorized continuation. Transfer cases include repeated restore,
missing and same-path backups, changed authority epochs and preserved work after failed preflight.
The operational runbook should list what to inspect before explicitly resuming.

This notebook performs local restore experiments. A **service manager**, such as systemd on a
supported Linux host, starts and supervises long-running services. A unit file describes a service;
restart policy, permissions and boot behavior require host-specific verification. The core's
local PASS is not a host reboot, upgrade or unattended-service acceptance claim. Keep the book's
host recipe as a separately observed extension.
