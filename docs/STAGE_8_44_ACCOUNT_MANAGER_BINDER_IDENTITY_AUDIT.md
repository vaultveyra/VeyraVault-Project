# Stage 8.44 — AccountManager Binder identity and asynchronous scope audit

Status: read-only source audit and CI guard. No Engine runtime/AIDL patch, account migration, or user-data operation is included.

Audited VeyraVault head: 8d43b70c950fd182e4298e3f7391aee139d8a493
Pinned Engine: ALEX5402/NewBlackbox@89b59836c66f173756a4ae258cf379a957649820

## Product identity decision

Preserve VeyraVault's existing Space semantics. The numeric virtual userId remains the Space identity and may be shared by different app packages intentionally. A Clone/account scope is the composite tuple:

`(virtualPackageName, virtualUserId)`

Do not globally renumber Space IDs or change the package-scoped Clone allocator to work around AccountManager's storage mismatch.

## Additional source findings

### Trusted Binder identity is available, but not consistently used

The pinned Engine's BAccountManagerService has a helper that reads Binder.getCallingPid(), resolves that PID through BProcessManagerService.findProcessByPid(), and obtains ProcessRecord.getPackageName(). ProcessRecord also carries the virtual userId.

This is a viable trusted identity source at the synchronous Binder entry point. The current helper does not validate that the resolved ProcessRecord.userId matches the userId argument supplied to the service method. A future implementation must validate both package and virtual user identity and fail closed if the process record is absent, stale, or mismatched.

Do not call Binder.getCallingPid() later from an asynchronous authenticator callback and assume it still identifies the original app. Capture a validated immutable AccountScope at Binder entry and pass it explicitly through every asynchronous Session and callback.

### getAuthToken currently trusts a Bundle package field

The current getAuthToken implementation reads AccountManager.KEY_ANDROID_PACKAGE_NAME from loginOptions and uses that value as callerPkg for the custom TokenCache. That value is request data, not proof of Binder caller identity. The method also forwards loginOptions to the authenticator.

Future package-scoped logic must derive the caller package from the validated Binder ProcessRecord, replace or validate the package field before forwarding options, and use the captured AccountScope for both persistent and in-memory token paths. A caller-supplied Bundle value must never select another Clone's bucket.

### Asynchronous Session currently retains only the numeric bucket

The current inner Session retains BUserAccounts in mAccounts, but has no package identity or immutable scope object. Its authenticator bind, result callback, token persistence and account-presence checks can outlive the original Binder call.

The new scope must be captured when the Session is created and remain attached through result/error, token cache, persistent token write, account visibility and authenticator callback paths. Authenticator package identity is not a substitute for the requesting Clone identity.

### Listener methods are currently empty

BAccountManagerService.registerAccountListener and unregisterAccountListener have empty bodies in this Engine pin. Do not claim listener registration or per-Clone change-notification isolation is implemented. A future implementation must key listener registrations by the validated AccountScope and clean them up on Binder death/process death.

## Required implementation boundary

Before changing Engine runtime code, complete a method-by-method matrix across IBAccountManagerService AIDL, BAccountManager facade, IAccountManagerProxy hooks, BAccountManagerService, BUserAccounts, BAccount, TokenCache and Session. Every operation must resolve one validated AccountScope, including:

- account add/remove/copy and enumeration;
- account visibility and app permission;
- password and user-data read/write;
- persistent auth-token read/write/invalidation;
- custom TokenCache read/write/invalidation;
- authenticator sessions, callbacks and account-presence checks;
- listener registration, notification and death cleanup.

Do not trust a packageName supplied only by a method argument or Bundle as the caller's identity. For APIs that legitimately address another package's visibility, distinguish the target visibility package from the caller's AccountScope and apply explicit authorization.

## Legacy persistence rule

The existing accounts.conf map is keyed only by numeric userId. Existing BUserAccounts/BAccount records do not contain an authoritative Clone package owner. Package visibility entries and authenticator metadata are not sufficient proof of account ownership.

Keep legacy numeric buckets byte-for-byte preserved and unresolved where ownership is ambiguous. Do not split, copy, re-key, delete, or auto-assign existing accounts, passwords, user data, tokens, sessions, or caches. A future migration requires a separately reviewed, user-directed process with backup, rollback and process-death tests.

New package-scoped persistence must be versioned and separate from legacy data until compatibility and rollback are proven. No migration or dual-write is authorized by this audit.

## Synthetic validation required before implementation is considered complete

Use disposable synthetic packages, fake Accounts and sentinel values only:

1. Same numeric userId, package A vs package B: every direct read/write and token operation is isolated.
2. Same package, two userIds: independent buckets.
3. Caller-supplied Bundle package spoofing is rejected or overwritten by trusted Binder identity.
4. ProcessRecord userId mismatch, missing PID mapping and stale process mapping fail closed.
5. Authenticator callback after the original Binder call retains the original AccountScope.
6. Persistent authTokens and custom TokenCache are both isolated.
7. Account visibility and permission APIs cannot cross the caller's scope.
8. Listener delivery and unregister/death cleanup are scope-specific.
9. Process restart/reload preserves each new composite bucket.
10. Legacy numeric account data remains byte-for-byte unchanged and inaccessible to ambiguous new scopes unless an explicit migration policy is approved.

## Explicit non-actions

No Engine runtime/AIDL source, CloneStore allocator, Space ID, Clone ID, reservation, account record, credential, token, session, cookie, app-private data, Room state or main-branch content was changed. No global ID allocator, account migration, cleanup or deletion was performed.

PR #4 remains open, Draft and unmerged. main remains unchanged.
