# Stage 8.42 — AccountManager package-scoped storage design

Status: architecture decision and test plan only; no Engine runtime/AIDL changes in this stage.

## Product invariant to preserve

VeyraVault's `userId` is the logical Space ID plus one. Multiple app packages may intentionally occupy the same Space and therefore share the same numeric Engine userId. The package-scoped CloneStore allocator is part of that product behavior and must remain unchanged.

## Problem confirmed in pinned Engine source

The pinned Engine AccountManager service persists `Map<Integer, BUserAccounts>` keyed only by numeric userId. Direct APIs such as password, user-data and persistent auth-token reads/writes resolve this numeric bucket without adding package identity. Package-aware listing applies visibility, but that does not prove direct credential isolation.

The custom in-memory TokenCache already includes packageName in its matching key. The persistent `BAccount.authTokens` map is still keyed by Account and token type under the numeric user bucket.

## Target identity

For new AccountManager operations, the effective account scope must be the trusted tuple:

`(virtualPackageName, virtualUserId)`

The package name must be derived from the active virtual process/Binder caller identity (for example the Engine's PID-to-virtual-process lookup). Do not trust a package name supplied only through a Bundle or caller argument.

## API families requiring one consistent scope

The audit and synthetic tests must cover:
- addAccountExplicitly and account removal
- getAccounts, getAccountsByType, getAccountsForPackage and visibility
- getPassword/setPassword
- getUserData/setUserData
- peekAuthToken/setAuthToken/getAuthToken
- persistent auth-token read/write
- custom TokenCache lookup and invalidation
- updateAppPermission and account listeners
- authenticator/session callbacks and any API that re-enters the service

Direct credential APIs must not reach another package's bucket merely because the two packages share a Space/userId. Listing visibility remains an additional filter, not the only security boundary.

## Legacy data rule

Existing `accounts.conf` records are keyed only by numeric userId. If multiple packages share a userId, the old bucket cannot be safely attributed to one package. Do not copy, split, delete, re-key or auto-assign those account records. Preserve them and report the ownership as unresolved. A later migration may be offered only after a user-directed choice or another independently verified ownership source.

For a userId with exactly one known package, a compatibility migration may be designed, but it still requires backup/rollback, process-death tests and explicit approval before production activation.

## Required synthetic tests

Use only synthetic package names, fake Accounts and sentinel passwords/tokens:
1. Two packages with the same numeric userId cannot read/write each other's password, userData or persistent authTokens.
2. One package with two userIds has independent buckets.
3. Listing visibility and direct credential APIs are tested separately.
4. TokenCache package scope and persistent authTokens are both tested.
5. Process restart preserves each package/user bucket independently.
6. Remove/reinstall one package does not erase another package's bucket.
7. Legacy numeric buckets remain byte-for-byte preserved when ownership is ambiguous.
8. Binder caller identity cannot be spoofed with a Bundle package name.

No real accounts, passwords, userData, tokens, sessions or Clone data may be read or modified during these tests.

## Non-goals

No global Clone ID allocator. No Space renumbering. No Room activation. No account migration or cleanup. No changes to CloneStore allocation. Session, cookie, database and SharedPreferences isolation capabilities remain NOT_IMPLEMENTED until separate runtime and physical-device evidence exists.
