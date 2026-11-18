# Stage 7.9.8 — Atomic Clone ID Reservation Design Audit

## Status

Design/audit only. No runtime code, stored clone record, virtual package, account/session data, or Engine state is changed by this document.

Target branch: `feat/veyra-vault-product-foundation`  
PR: #4 (must remain Draft, open, and unmerged).

## Verified current behavior

- `AsyncCloneRepository.allocateNextUserId(packageName)` reads the strict CloneStore registry and returns the first unused package-scoped virtual user ID.
- The operation is serialized only by the executor belonging to that particular repository instance.
- The returned ID is not held or reserved while the caller performs Engine installation and later persists the clone.
- `AddAppActivity` and `MainActivity` now use the async repository for allocation and preserve Engine-install-before-registry-write ordering.
- `CloneStore.nextFreeUserIdForPackage` remains a synchronous lookup API. It is fail-closed on corrupt registry data but does not reserve an ID.
- `CloneStore.upsertClone` persists a new or existing record without a reservation token.
- The public `AsyncCloneRepository(Context)` constructor means more than one repository instance can exist; a single-thread executor per instance is not a process-wide mutual-exclusion guarantee.
- The current UI operation guard is local to an Activity instance and cannot protect against a second Activity or another repository instance.

## Race condition

Two independent operations can both read the same registry snapshot before either persists its new clone:

1. Operation A allocates package P / user ID N.
2. Operation B allocates package P / user ID N.
3. Both ask the Engine to install P / N.
4. Both attempt to persist the same composite identity.

The current code has no reservation state that spans steps 1–4. A successful CI run does not prove this race is impossible.

## Required invariants for the next implementation

1. A package/user composite identity can have at most one active creation reservation within the supported coordination scope.
2. Reservation acquisition must be atomic relative to every other reservation acquisition and every clone-registry mutation that could create the same identity.
3. A reservation is bound to package name, user ID, and an opaque unique token; callers cannot commit or release another operation's reservation.
4. Engine installation remains before the committed CloneStore record. Do not create a visible clone record before Engine installation is confirmed.
5. Successful reserved persistence must consume the reservation as part of the same durable commit that writes the clone record.
6. Engine install failure releases the reservation.
7. If persistence fails after Engine install, release is allowed only after Engine uninstall is explicitly confirmed. Unknown/unconfirmed cleanup must retain a blocking reservation or enter an explicit recoverable state.
8. A process restart must not silently make an identity available if an Engine installation from an interrupted operation may still exist.
9. Unknown/corrupt reservation data fails closed; it must never be treated as an empty reservation set.
10. Existing clone records, legacy preference keys, app-private virtual data, accounts and sessions must remain untouched by tests.

## Design options and decision gates

### Option A — process-memory reservations

A static process-wide lock and reservation map could coordinate all repository instances in the host app process without adding persisted data. This is simpler, but reservations disappear on process death. If Engine installation completed just before process death and registry persistence did not, the next process could reuse an identity while an orphan virtual installation remains. This option alone is insufficient unless Engine state is also authoritatively checked during recovery/allocation.

### Option B — durable reservation journal

A versioned reservation journal can preserve pending identities across process death. The design must specify:
- strict schema/version validation and token ownership;
- atomic acquisition against clone-registry reads/writes;
- atomic clone-record commit plus reservation consumption;
- safe handling of interrupted operations;
- a recovery path that uses tri-state Engine inspection (installed / absent / unknown);
- no automatic destructive uninstall when Engine state is unknown;
- explicit handling of stale reservations without unsafe time-based expiry.

A time-to-live alone is not a safe recovery mechanism: an operation that is still installing could outlive the lease and collide with a second allocator.

### Option C — Room-backed reservation table

Room is currently inactive and intentionally disconnected from runtime. Activating it only for ID reservation would introduce a second persistence authority and a partial migration dependency. Do not choose this without a separate architecture review and an explicit migration plan.

## Recommended direction

Prefer a durable reservation journal only if its coordination and recovery semantics can be implemented without activating Room or changing the existing CloneStore source of truth. The reservation ledger should be operational metadata, not a replacement for the clone registry.

Before coding, verify whether the reservation journal can be committed atomically with the clone JSON in the same SharedPreferences file/editor while preserving every existing key. If not, do not claim atomic commit across stores; redesign the transaction boundary rather than relying on two independent commits.

The recovery path must be conservative:
- Engine reports the reserved package/user absent: the reservation may be released.
- Engine reports it installed while no clone record exists: keep the identity blocked and surface a recoverable orphan state; do not silently reuse it.
- Engine query fails or returns an unknown result: retain the reservation and report unresolved state.
- Clone record exists with matching identity: treat the registry as authoritative only after verifying token/journal consistency; repair must be explicit and tested.

## Required API shape (conceptual)

- `reserveNextUserId(packageName, callback)` → opaque reservation object.
- `commitReservedClone(entry, reservation, callback)` → writes the clone and consumes exactly that reservation.
- `releaseReservation(reservation, callback)` → only for the matching token and only when Engine state makes release safe.
- `loadPendingReservations(callback)` and a conservative recovery operation for diagnostics/recovery UI.

The old lookup-only allocator must not remain in any clone-creation caller after adoption. If retained for compatibility, document it as non-reserving and prohibit using it for installation flows.

## Test gates

- Two concurrent reservation requests for the same package from separate repository instances receive distinct IDs.
- Concurrent requests for different packages retain package-scoped identity semantics.
- Reservation tokens cannot be reused, forged, or used for another package/user pair.
- A failed reservation commit returns no usable reservation.
- A failed clone commit does not consume the reservation.
- Successful clone commit writes the clone and consumes the reservation in one verified durable commit.
- Engine install failure releases only its own reservation.
- Unconfirmed uninstall retains the reservation.
- Process-death/restart recovery distinguishes absent, installed, and unknown Engine states.
- Corrupt/unsupported reservation journal data blocks allocation and is never overwritten.
- Legacy clone records and all existing preference keys remain byte-for-byte unchanged except the intended clone-registry commit for a successful new clone.
- Run source contracts, Android Emulator instrumentation, Source Audit, release APK compilation and APK Audit.
- Physical-device concurrency and interrupted-install recovery remain required before production reliance.

## Explicit non-goals

- No Room activation or migration/cutover.
- No change to Engine install/uninstall semantics beyond a narrowly reviewed query adapter if required.
- No automatic deletion of clone data or virtual app package data.
- No app account/session backup or restore.
- No change to `main`, no PR merge, and no broad UI redesign.
