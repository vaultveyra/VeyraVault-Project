# Stage 8.41 — Global monotonic Clone ID allocation

Status: implementation added on the feature branch; CI and Android instrumentation validation required before rollout.

Parent: 78c551f74c69e2e863c3d82909d51e21b7c6f149  
Branch: feat/veyra-vault-product-foundation  
PR #4 remains Open, Draft and Unmerged.

## Change

New Clone creation now requires both read-only Engine inventories before reserving an ID: Engine virtual-user IDs and numeric AccountManager bucket keys. The calls run on the single Engine operation queue. If either inventory cannot be read, is malformed, contains duplicate/negative IDs, or the Engine queue rejects the operation, provisioning stops before ID reservation and before package installation.

CloneStore computes the maximum across current Clone registry IDs, pending reservation IDs, Engine virtual-user IDs, AccountManager numeric bucket IDs, and the existing durable high-water mark. The next candidate is max + 1. Integer overflow fails closed. The pending reservation and new high-water mark are persisted in one SharedPreferences commit before Engine installation.

## Lifecycle guarantees

- Commit consumes only the exact token-bound reservation; the high-water mark is not reduced.
- Confirmed failure may remove the pending reservation, but never lowers the high-water mark.
- Removing a Clone registry row never lowers the high-water mark.
- New allocations cannot reuse any ID represented in verified inventories or durably reserved after ledger initialization.
- The old package-scoped nextFreeUserIdForPackage helper is deprecated and is not used by production provisioning.

## Legacy boundary

No existing Clone identity, app data, account, token, cookie, session, or Engine user is modified.

If an old ID was already completely erased from the Clone registry, reservation journal, Engine virtual-user inventory and AccountManager inventory before this ledger is initialized, no remaining source can reconstruct it. The initial high-water mark is seeded from the maximum still-verifiable inventory. This prevents reuse of known IDs and IDs reserved after initialization; it cannot prove lifetime non-reuse for unknown legacy IDs that disappeared from every store before rollout.

Existing cross-package duplicate IDs remain visible in Stage 8.39 diagnostics. They are not split, remapped, or deleted. The global allocator prevents future newly allocated Clones from creating additional numeric collisions, but it does not repair current AccountManager buckets shared by legacy Clones.

## Safety and validation

Synthetic tests use only disposable package names and test-isolated preferences. They cover cross-package uniqueness, all inventory sources, high-water persistence, release/removal monotonicity, invalid inventory rejection and integer overflow.

No real Engine account or credential is accessed by these tests. Real-app AccountManager cross-package access and session isolation remain unverified; capability flags stay NOT_IMPLEMENTED.

## Non-actions

No Room activation. No Engine AIDL/runtime modification. No global cleanup. No ID release/reuse/remap of existing Clone records. No call to user-wide deleteUser. No changes to main. No signing claim for the CI APK.
