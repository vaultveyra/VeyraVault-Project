# Stage 8.40 — AccountManager direct-API package-scope gate

Status: source audit and CI guard added; runtime package-scope test remains required.

VeyraVault branch: feat/veyra-vault-product-foundation  
Audited parent: 6acac93e18fd36861f9c0e3a0809859cfb2372ed  
Pinned Engine: ALEX5402/NewBlackBox at 89b59836c66f173756a4ae258cf379a957649820

## Purpose

Stage 8.39 connected numeric-only AccountManager inventory to Settings diagnostics. Stage 8.40 adds a precise audit of the AccountManager Binder route, direct credential/token APIs, persistent tokens, custom TokenCache and the dormant GoogleAccountManagerProxy code.

This is a source blocker gate, not an account-isolation implementation.

## Findings

### Persistent bucket identity

The pinned service stores BUserAccounts in an Engine-wide map keyed by Integer userId. Account records are nested under that bucket. BAccount contains account, password, userData, visibility and authTokens; it has no packageName identity field.

The direct getPassword, getUserData, peekAuthToken, setAuthToken, setPassword and setUserData service methods resolve a bucket using getUserAccounts(userId). Their persistent lookup/write paths do not add packageName or a trusted Binder-derived caller package to the storage key.

### Listing visibility is not credential isolation

Package-aware listing methods such as getAccountsForPackage and getAccountsByTypeForPackage apply each account's package visibility map. This restricts enumeration.

It does not establish that direct password, userData, persistent auth-token or account mutation APIs use a package-specific bucket. A listing test alone is insufficient.

### Two different Token paths

The in-memory custom TokenCache compares userId, Account, token type and packageName. The persistent authTokens map in BAccount is stored by Account and token type under the numeric userId bucket, without packageName in the key.

The audit therefore treats custom-token cache matching and persistent AccountManager token storage as separate boundaries. getAuthToken receives a caller package value for its custom cache path, but its persistent token lookup calls readAuthTokenInternal on the userId bucket.

### AccountManager hook path

HookManager registers IAccountManagerProxy, whose Binder injection replaces the virtual ACCOUNT_SERVICE and routes methods through BAccountManager. The facade supplies BActivityThread.getUserId() to the Engine service. This is the active AccountManager proxy path found in the pinned source.

HookManager also registers GoogleAccountManagerProxy. Its current inject() implementation is empty. ClassInvocationStub constructs an in-memory dynamic proxy and calls inject(), but this class does not install or publish that proxy. The source contains mock fallback values, but the audit does not treat those hooks as active in this pinned wiring. Any future change to inject() requires review because it could activate those mock responses.

## Why the collision remains a blocker

CloneStore identity and allocation are packageName + userId, while AccountManager persistence is numeric userId only. Different Clone packages can therefore share the same AccountManager bucket. Stage 8.39 reports numeric overlaps but does not repair or reassign them.

## Safe remediation paths to evaluate

1. **Globally unique IDs for future Clones.** Allocate from a durable monotonic high-water mark. Before reserving, require successful inventories from CloneStore, pending reservations, Engine virtual users and AccountManager numeric keys. Any unavailable or malformed inventory must block allocation. Never reuse a previous ID. This prevents new cross-package numeric collisions but does not automatically repair existing duplicates.
2. **Composite AccountManager bucket identity.** Change service storage to a trusted packageName + userId identity, deriving package identity from the Binder caller/virtual process rather than trusting a caller-supplied Bundle field. Every read, write, listener, authenticator callback, cache and visibility path would need the same identity contract. This is a deeper Engine migration.
3. **Legacy collision handling.** If multiple current Clone packages share one numeric AccountManager bucket, the existing bucket cannot be safely attributed to one package from the numeric map alone. Do not split, copy, delete or move old account records automatically. Preserve the bucket and mark ownership unresolved until a separately reviewed, user-directed migration exists.

No remediation path is activated by this stage.

## CI contract

The Stage 8.40 source gate checks:
- direct credential/token methods use the numeric user bucket without package identity;
- package visibility is applied separately to package-aware listing;
- custom TokenCache and persistent authTokens have different package-scope keys;
- the active Binder proxy and userId facade route are identified;
- GoogleAccountManagerProxy's current empty injection is not misrepresented as active;
- isolation capability flags remain NOT_IMPLEMENTED.

A PASS means the source boundary was detected accurately. It is not a pass for account/session isolation.

## Explicit non-actions

No account name, password, userData, token, visibility value or session was read from the running Engine. No Engine runtime behavior or AIDL was changed. No CloneStore record, Clone ID, reservation, account bucket, credential, cookie, session or app-private data was changed. No global allocator was activated. Room remains inactive.

PR #4 remains Open, Draft and Unmerged; main is not modified.

## Required next stage

Stage 8.41 must prototype and review a non-destructive new-Clone identity strategy, then test with synthetic package names and synthetic accounts:
- same numeric userId across two package names;
- one package with two different virtual userIds;
- package-aware account listing visibility;
- direct password/userData/persistent auth-token API boundaries;
- custom TokenCache versus persistent authTokens;
- process restart and account-map reload;
- uninstall/reinstall without deleting another Clone's bucket.

Runtime and physical-device validation remain required before any isolation capability is marked supported.
