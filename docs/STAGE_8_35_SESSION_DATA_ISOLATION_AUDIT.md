# Stage 8.35 — Session and account data isolation audit

Status: source audit completed; a cross-package virtual AccountManager scope mismatch is confirmed. No production Engine/runtime behavior, clone identity, or user data was changed.

Audited sources:
- VeyraVault branch: feat/veyra-vault-product-foundation
- VeyraVault audit head: a9c0ac1d2ad62ae682d0ee1d577bbb97f773de99
- Pinned Engine: ALEX5402/NewBlackbox at 89b59836c66f173756a4ae258cf379a957649820
- Engine source pin remains controlled by scripts/prepare_workspace.py.

## 1. Findings

### 1.1 App-private data paths are package and virtual-user scoped

The pinned BEnvironment maps app data to separate roots using both packageName and userId:
- internal credential-protected data: data/user/<userId>/<packageName>
- device-protected data: data/user_de/<userId>/<packageName>
- external app data: storage/emulated/<userId>/Android/data/<packageName>
- external OBB: storage/emulated/<userId>/Android/obb/<packageName>
- databases, files, cache and lib directories are children of the corresponding package/user directory.

This is positive structural evidence for ordinary app-private files, databases and SharedPreferences. It is not a complete runtime proof: a device/emulator test must still create different sentinels in two Clone processes and verify no cross-read, including after process death and relaunch.

### 1.2 Engine AccountManager state is virtual-user scoped, not Clone-pair scoped

The pinned Engine stores its account registry in one Engine-wide system file, accounts.conf. BAccountManagerService loads and saves a map keyed by Integer userId. Its getUserAccounts(int userId) lookup uses only that integer. BUserAccounts contains the account records, passwords, user data, auth-token values and visibility metadata.

The AccountManager service APIs and BAccountManager facade pass BActivityThread.getUserId(); they do not add the current package name to the persistent account-store key. Package visibility is tracked within account records and listing APIs apply that visibility filter. However, direct operations such as getPassword, getUserData, peekAuthToken, setAuthToken and getAuthToken are dispatched through the facade with the virtual userId and account handle, without adding a package-scoped storage key. Persistent auth-token values are stored in the BAccount record by token type. Thus the account collection is shared by userId; visibility can restrict enumeration, so this audit does not claim that every Clone can automatically list every other Clone's accounts. A synthetic runtime test is required to establish the precise read/write boundary for each API.

### 1.3 VeyraVault currently allocates numeric user IDs independently per package

CloneStore.reserveNextUserId and nextFreeUserIdForPackage build the used-ID set using only entries and reservations with the requested packageName. The registry's uniqueness key is the pair packageName + userId.

Consequently, two different package names can legitimately receive the same numeric userId (for example, each package's first Clone can receive 0). Those Clone records are distinct in VeyraVault but resolve to the same Engine virtual-user AccountManager collection.

This establishes a scope mismatch:
- VeyraVault Clone identity: packageName + userId
- Engine AccountManager identity: userId only

Depending on the app's AccountManager API calls and account visibility, credentials/account data may be reused across different package Clones that share a numeric userId. This is not evidence that every app's private database or app-local session token is shared; those remain package/user-path scoped. It is sufficient to prevent a blanket claim that all account/session state is Clone-isolated.

### 1.4 Package-scoped uninstall, account retention and numeric ID reuse

VeyraVault Engine.uninstallClone calls the pinned Engine uninstallPackageAsUser(packageName, userId) API and then checks package/user data directories. It does not call deleteUser(userId).

The pinned BAccountManagerService package-uninstall callback reloads authenticator metadata; it does not remove the BUserAccounts object or purge that userId's account records from accounts.conf. The package-scoped Engine uninstall removes the selected package/user app-data directories and package user-state entry, but does not remove the BUserInfo virtual-user record from BUserManagerService.

CloneStore.removeClone removes the package/user registry row without writing a permanent retired-ID tombstone. The package-scoped nextFreeUserIdForPackage allocator then chooses the lowest free number again. This is independently covered by a synthetic Android instrumentation test. Together, these source paths mean an uninstalled Clone's AccountManager bucket can outlive its package data and its numeric userId can later be assigned again, including to a different package. A recreated Clone may therefore encounter old virtual-user AccountManager records, subject to package visibility and API behavior.

The separate BUserManagerService.deleteUser(userId) path is not a safe per-Clone substitute: it asks BPackageManagerService to uninstall that user across all packages and deletes the entire internal and external virtual-user roots. Never invoke this user-wide operation to remove one VeyraVault Clone.

### 1.6 Read-only Engine virtual-user inventory

The pinned Engine exposes the AIDL IBUserManagerService.getUsers() method, backed by BUserManagerService.getUsers(). Each returned BUserInfo contains a numeric id. VeyraVault exposes this through Engine.getKnownVirtualUserIds(), which:
- resolves the BUserManager facade and obtains its Binder service directly;
- invokes getUsers() through the public AIDL interface instead of BlackBoxCore.getUsers(), whose facade can turn service failures into an empty list;
- reads only each BUserInfo.id field;
- validates service availability, interface type, null entries, negative IDs and duplicates;
- returns a sorted immutable list;
- fails explicitly if the Engine, Binder service or method is unavailable.

The Settings Clone Identity diagnostics compares three read-only views:
- cross-package duplicate IDs in the strict current Clone registry;
- Engine user IDs with no matching current Clone registry row;
- Clone registry IDs not present in the current Engine user list.

An Engine-only ID is not automatically free: package-scoped uninstall removes that package's user-state/data but leaves the virtual BUserInfo entry. Such an ID may represent an old Clone whose registry record was removed. A Clone-only ID is also not repaired automatically.

Important limitation: BUserManagerService.deleteUser removes the Engine BUserInfo entry and user data roots, but the pinned BAccountManagerService does not show a corresponding purge of its accounts.conf map. Therefore the Engine user list cannot reveal account buckets left behind by a historical full virtual-user deletion. An ID absent from both the current Clone registry and Engine user list must not be assumed safe to reuse until the AccountManager orphan-retention policy is addressed. The diagnostics page says this explicitly and never releases IDs.

### 1.5 WebView has an active process-scoped suffix; persistence still needs runtime proof

The pinned BActivityThread creates the package Context and, on Android 9 / API 28 and newer, calls:

    WebView.setDataDirectorySuffix(getUserId() + ":" + packageName + ":" + processName);

The call occurs before VirtualRuntime setup and before the virtual target Application is created. It uses the virtual user ID, package name and process name (not the transient PID), which is the active WebView data-directory separation mechanism in this Engine revision.

A separate WebViewProxy class exists in the source but is not registered in HookManager. Do not mistake that unused class for the active mechanism; the active source path is BActivityThread.

This is positive source-level evidence, not an end-to-end persistence certification. CookieManager, DOM storage, WebView databases and process-restart persistence still require synthetic target-app tests on API 28+ and on older supported APIs where this suffix API is unavailable.

## 2. Current VeyraVault status

The 97-field ProfileFieldRegistry correctly classifies sessionDataIsolation, cookieStorageIsolation, databaseIsolation, sharedPreferencesIsolation and related unverified storage fields as NOT_IMPLEMENTED. Keep those classifications. A value stored in a profile document is not proof that the Engine enforces it.

The current Engine wrapper uses package/user-scoped uninstall. It does not call the broader Engine deleteUser path. Preserve this boundary.

## 3. Non-destructive validation design

Use synthetic test packages/accounts only. Never use an existing user Clone, real account, real token, message history or production app-private directory as a failure-injection fixture.

Required matrix:
1. Same package, two different virtual user IDs: write unique sentinels to app files, databases, SharedPreferences, DE data and account APIs; assert no cross-read.
2. Different package names, the same numeric userId: demonstrate and then close the AccountManager scope mismatch before claiming isolation.
3. Package-scoped uninstall followed by a fresh Clone: verify whether account state remains for the numeric userId; no production Clone may be uninstalled for this test.
4. Process death and Engine restart: verify that app-local session state persists only in its own package/user directory and that account visibility and auth-token behavior remain correct.
5. WebView test on supported Android versions: create different test cookies, DOM storage and IndexedDB/database markers; restart the virtual process and verify both separation and persistence.
6. Global user deletion guard: prove that deleting a virtual user is never used for a single package Clone and would affect all packages sharing that userId.

The source-contract audit added with this stage is intentionally read-only. It verifies the current architecture and prints the known blocker; it does not claim that the blocker is fixed and does not access a running Engine's accounts.conf or any Clone data.

## 4. Architecture decision required before runtime changes

Two viable directions require separate design review:

A. Keep package-scoped Clone IDs and make AccountManager storage explicitly package/user scoped. This requires an end-to-end review of the AccountManager AIDL, framework proxies, BAccountManager facade, service/session/token code, account visibility semantics and compatibility with apps that intentionally share accounts.

B. Move to globally unique virtual user IDs per Clone. This requires a durable, never-reuse allocation ledger and a read-only collision inventory. Existing Clone IDs must not be silently reassigned: moving an existing Clone would involve Engine user state, profile records, active-launch markers, reservations and app-private data. No automatic migration or destructive cleanup is authorized by this audit.

Do not select either direction solely from source inspection. First produce a read-only inventory of duplicate numeric user IDs across package names and run isolated synthetic AccountManager tests. Then approve a migration/compatibility design that preserves every existing Clone and account.

## 5. Acceptance criteria for sessionDataIsolation

Do not promote sessionDataIsolation to APPLIED until all of the following pass:
- package/user identity is consistently enforced for app-private and AccountManager state;
- account, password, user-data, auth-token and visibility operations cannot cross Clone boundaries except through an explicitly documented shared-account policy;
- app files, databases, preferences, DE data, external data and WebView storage pass synthetic cross-Clone tests;
- process death, Engine restart, uninstall/recreate and ID-reuse tests pass;
- API 21, API 27 and current supported Android emulator/device tests pass;
- tests prove existing Clone data remains unchanged.

No Room activation, CloneStore migration, ID reassignment, Engine pin change, session reset, account deletion or main-branch change is part of Stage 8.35.
