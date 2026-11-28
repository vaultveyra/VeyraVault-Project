# Stage 8.38 — Read-only AccountManager numeric user-ID inventory

## Purpose

Stage 8.35 identified that the pinned Engine persists AccountManager buckets in `accounts.conf` as a map keyed by the numeric virtual `userId`. The map can retain historical/orphan keys that are no longer present in the Engine's current virtual-user list. A future never-reuse allocator must therefore inspect these keys before it can safely choose an unused numeric ID.

This stage adds a narrowly scoped, read-only inventory API. It does **not** enable or change ID allocation.

## Implementation boundary

After `prepare_workspace.py` verifies the exact pinned upstream Engine checkout, it applies the patch only inside the disposable `build_workspace` used by CI:

1. Add `int[] getKnownAccountUserIds()` to the pinned `IBAccountManagerService` AIDL interface.
2. Track whether the persisted AccountManager map loaded successfully. A missing initial `accounts.conf` is treated as a valid empty store. An unreadable file, parse failure, null map, invalid key, negative ID or invalid bucket value leaves the load status unconfirmed.
3. Validate the entire deserialized map into a temporary map before replacing the in-memory map. The inventory is not marked successful until that full validation and in-memory snapshot commit complete.
4. The Binder method returns only sorted numeric map keys. It throws `RemoteException` when the load state is unconfirmed or an invalid bucket is found; it never reports an uncertain state as an empty array.
5. `Engine.getKnownAccountUserIds()` resolves the exact AccountManager Binder interface, validates the returned IDs, and returns an immutable sorted list. It does not substitute another API or catch failures as an empty inventory.

## Data and safety guarantees

- The inventory method reads only map keys and bucket presence.
- It does not return account names/types, passwords, userData, visibility values, auth tokens, or session content.
- It does not call `saveAllAccounts()`, remove accounts, clear token caches, uninstall a package, delete a virtual user, or mutate the persisted `accounts.conf`.
- Existing map contents are not replaced until the complete persisted map has passed validation.
- The API is not used by Clone ID allocation in this stage. The current package-scoped allocator remains unchanged.
- This stage does not reassign any existing Clone ID, create tombstones, clean orphan records, activate a global allocator, enable Room, or change `main`.

## Verification

The Stage 8.38 fixture test checks AIDL and service patch shape, fail-closed load status, complete-map validation before in-memory replacement, sorted numeric-only results, absence of account-data mutation, idempotence, and source-drift rejection before either Engine source file is written.

The Stage 8.35 source audit also verifies that the new service API and VeyraVault wrapper exist, while the account/session isolation capabilities remain `NOT_IMPLEMENTED`.

These are source-contract and fixture checks. They do not inspect a user's live `accounts.conf` and do not prove end-to-end account/token isolation. The cross-package numeric-ID collision remains a known architectural blocker until the allocator design and synthetic runtime tests are completed.

## Next gate

Before enabling a global, monotonic ID allocator, add an ID-only runtime test covering synthetic account buckets, persisted orphan keys and process restart. Then combine this AccountManager inventory with CloneStore registry IDs, pending reservations and Engine virtual-user IDs. Any unavailable or corrupt inventory source must block allocation; existing Clone IDs remain untouched.
