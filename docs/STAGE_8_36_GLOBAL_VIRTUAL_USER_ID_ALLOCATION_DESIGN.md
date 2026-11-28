# Stage 8.36 — Global virtual user ID allocation design

Status: architecture proposal only. No allocator, Engine AIDL, Clone ID, AccountManager record, or existing user data was changed by this document.

## 1. Decision

For newly created Clones, prefer globally unique, monotonically increasing Engine virtual user IDs rather than restarting the numeric sequence independently for each package.

The Clone registry may continue to identify a Clone by (packageName, userId), but every newly allocated userId must be unique across all packages and must never be reused after it has been durably reserved.

This aligns the three relevant scopes:
- VeyraVault's Clone identity: (packageName, userId);
- Engine app-private storage: (userId, packageName);
- Engine AccountManager storage: userId.

It avoids adding package identity to every Android AccountManager API, authenticator callback, account visibility operation and auth-token cache path. It does not retroactively separate existing Clones that already share one numeric ID.

## 2. Why a CloneStore-only maximum is insufficient

The current CloneStore registry and reservation journal cover currently registered/pending Clone identities, but:
- removing a Clone row removes its ID from the active registry;
- the current package-scoped allocator can return that number again;
- package-scoped Engine uninstall does not delete the BUserInfo virtual-user record;
- BAccountManagerService stores account state in one Engine-wide accounts.conf map keyed by userId;
- the pinned BUserManagerService.deleteUser(userId) removes the BUserInfo entry and user data roots, but the pinned BAccountManagerService has no corresponding user-removal purge for its mUserAccountsMap.

Therefore an ID may be absent from both the current Clone registry and the Engine BUserManager user list while an AccountManager map entry still exists. A global allocator must know about that map before it can claim lifetime non-reuse.

## 3. Required read-only ID inventory

Before enabling global allocation, expose the following Engine inventories. These APIs return only numeric user IDs; they must never return Account, password, user-data, auth-token or visibility values.

1. CloneStore current IDs across every package.
2. All pending Clone reservation IDs across every package.
3. Engine BUserManager getUsers() IDs, using a direct Binder-service query that fails closed rather than accepting a facade fallback to an empty list.
4. Engine AccountManager mUserAccountsMap keys loaded from accounts.conf, including IDs whose BUserInfo was deleted. Add a read-only AIDL method such as int[] getKnownAccountUserIds() to BAccountManagerService and the BlackBoxCore facade. The implementation must snapshot the map keys under the existing lock and must not expose account contents.
5. The durable VeyraVault high-water mark described below.

If any required inventory is unavailable, malformed, duplicated, negative, or cannot be verified, new Clone ID reservation must fail before Engine installation. Do not interpret unknown as empty.

## 4. Durable monotonic reservation algorithm

Add a strict, versioned high-water mark in the existing app-private CloneStore persistence namespace, for example last_reserved_global_user_id.

Under the same process-wide reservation lock and repository serialization used by Clone creation:

1. Strictly read and validate CloneStore registry entries and pending reservation records.
2. Read the Engine BUserManager ID list and AccountManager user-ID key list.
3. Strictly read the durable high-water mark, if present.
4. Build a used-ID set from every registry, pending, Engine-user and AccountManager ID.
5. Select the first integer greater than both the high-water mark and the maximum known ID. Reject overflow; never wrap or return a negative ID.
6. Persist the pending reservation and the new high-water mark in one SharedPreferences Editor commit. The reservation must be durable before the Engine install call.
7. After a confirmed install, atomically commit the Clone registry row and consume only its owned reservation. The high-water mark is not reduced.
8. After a failed install, release the pending reservation only if the Engine explicitly confirms package/user absence and the relevant package/user data roots are confirmed absent. The high-water mark remains advanced.
9. If Engine state is unknown or cleanup is uncertain, preserve the reservation. Do not recycle the number.
10. Clone removal/uninstall never reduces the high-water mark and never makes an earlier number eligible again.

The high-water mark and reservation journal must be committed together. A process death before the commit leaves no reservation; a process death after the commit leaves a durable reservation and a monotonic high-water mark. A failed SharedPreferences commit must stop before Engine installation.

## 5. Existing Clone compatibility and migration boundary

- Do not change, normalize, reassign or migrate any existing Clone ID as part of enabling the new allocator.
- Existing cross-package duplicate IDs remain visible as a legacy collision in the diagnostic report.
- Existing Clones sharing one userId may still share the Engine AccountManager bucket. Do not claim that this design retroactively isolates them.
- New Clone creation may use an ID above all inventories, but it must not silently repair the existing collision group.
- Do not call Engine deleteUser(userId) to remove one Clone. That operation can affect all packages associated with the virtual user.
- Do not clear account records, cookies, databases or app-private directories during allocator migration.
- If an existing Clone needs a new ID, treat it as a separate explicit migration project requiring app-specific data export/import, profile/permission/active-launch reconciliation, install-state verification and user approval. No generic byte-copy migration is assumed safe.

## 6. AccountManager cleanup is a separate privacy lifecycle

A global never-reuse ID prevents a future Clone from inheriting an older account bucket, but does not erase that old bucket. AccountManager record cleanup requires a separate explicit lifecycle policy.

Any cleanup must prove that no installed package, current Clone row, pending reservation or active virtual process still uses the userId. The existing package-scoped uninstall API is not proof that an entire virtual user is unused. Do not automatically delete accounts during Clone uninstall.

## 7. Required validation

Use synthetic package names, synthetic accounts and disposable Engine user IDs only. Never use real user accounts or existing Clones for destructive fixtures.

Required tests:
- two different packages concurrently requesting IDs receive different global IDs;
- same package duplicate-clone flow also receives a new global ID;
- multiple repository instances and process-level reservation races cannot duplicate IDs;
- current Clone registry, pending journal, BUserManager IDs and AccountManager map keys are all included in the used set;
- an AccountManager-only orphan ID is never allocated, even when BUserManager no longer lists it;
- deleting a Clone registry row or uninstalling a package never makes a prior ID available again;
- process death before and after the atomic reservation/high-water commit recovers safely;
- failed install with confirmed absence releases only the reservation, not the high-water mark;
- failed/unknown Engine inventory, corrupt journal, corrupt high-water value and SharedPreferences commit failure all stop before Engine installation;
- Integer.MAX_VALUE exhaustion fails safely without wraparound;
- Android API 21, API 27 and current supported Android emulator tests pass;
- existing Clone registry/profile/active-launch snapshots remain byte-for-byte unchanged throughout the migration rehearsal.

## 8. Rollout gates

Do not switch the production allocator until:
- the AccountManager ID-only inventory API is implemented and audited against the pinned Engine source;
- all inventory sources are strict and fail closed;
- the monotonic ledger has process-death and concurrency instrumentation coverage;
- a read-only preflight has recorded existing Clone collisions and orphan IDs without exposing account contents;
- CI passes the full contract, API 21, API 27 and current-emulator suites.

Until those gates pass, preserve the current allocator and keep sessionDataIsolation, cookieStorageIsolation, databaseIsolation and sharedPreferencesIsolation as NOT_IMPLEMENTED.
