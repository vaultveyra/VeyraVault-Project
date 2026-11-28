# Stage 8.37 — AccountManager TokenCache virtual-user scope

Status: a source-level Engine defect was confirmed and a build-time hardening patch plus fixture test were added. The production Engine source pin is unchanged. No account, password, user data, auth token, existing Clone, or installed APK was modified.

## 1. Defect in the immutable Engine source

In the pinned BAccountManagerService:
- mUserAccountsMap is keyed by the requested integer userId.
- getUserAccounts(int userId) created new BUserAccounts() and inserted it under the requested map key, but did not set BUserAccounts.userId.
- loadAccounts() restored BUserAccounts Parcelable values from accounts.conf under their outer integer map keys, but did not reconcile the value's embedded userId with that key.
- BUserAccounts.userId is written to and read from Parcel, but its public no-argument constructor leaves the primitive field at its Java default.
- saveCachedToken() creates a TokenCache using accounts.userId.
- readCachedTokenInternal() compares a cache entry's userId against accounts.userId.

For nonzero Engine virtual users, the embedded value could therefore retain userId == 0 even when the outer AccountManager map key was a different number. The in-memory TokenCache scope then did not reliably follow the authoritative map key. Two virtual-user buckets using the same account handle, calling package and token type could collide in this cache path.

This is distinct from the already documented cross-package numeric ID collision: even distinct Engine user IDs require each BUserAccounts value to carry the correct matching ID for TokenCache to separate them.

## 2. Build-time hardening

After prepare_workspace.py verifies the exact clean pinned Engine commit, it applies the idempotent harden_account_manager_token_user_scope() patch only to the ephemeral build workspace:

1. While loading the persisted map, the outer integer key is validated and copied into BUserAccounts.userId before the value is inserted into mUserAccountsMap.
2. Every getUserAccounts(userId) lookup reassigns bUserAccounts.userId = userId from the requested map key before returning the value. This also repairs older in-memory Parcelable values when first accessed.
3. TokenCache continues using the existing accounts.userId field, but that field is now normalized from the actual bucket key.
4. The patch does not clear mTokenCaches, account records, auth-token maps, passwords, user data or visibility settings.
5. The patch does not change AIDL, public Android APIs, package visibility policy or persistent account identities.
6. Unexpected pinned source layout fails closed before the patched source file is written. The transformation is idempotent.

Existing persisted AccountManager data is not deleted or recreated. The in-memory derived userId field is corrected from the outer map key. If that value is serialized on a future ordinary AccountManager save, the corrected metadata is naturally persisted along with the existing records.

## 3. Validation

scripts/test_stage_8_37_account_manager_token_user_scope.py tests the exact build-time source transformation against isolated temporary source fixtures:
- correct embedded IDs are restored from the outer map key on load;
- new and existing buckets are normalized on every getter call;
- TokenCache construction and matching still use accounts.userId;
- original account-map and cache behavior is not replaced with clearing/recreation;
- the patch is idempotent;
- source drift fails without partially writing the fixture.

The Stage 8.35 source audit also asserts the patched load/get paths and TokenCache call sites. CI compiles and runs the Android suite against the prepared Engine workspace.

This is source/contract validation. It is not yet proof that real third-party authenticators, refresh flows, or simultaneous cross-user token requests behave correctly. A separate synthetic Engine integration test must exercise the same Account handle and package across two distinct virtual user IDs and prove each request receives its own token.

## 4. Safety boundary

- No existing Clone ID is changed.
- No account, password, user data, auth token, cookie, message or app-private file is read, exported, deleted or reset by this patch.
- No AccountManager cleanup or ID reuse policy is implemented here.
- No globally unique allocator is enabled.
- No Room activation or migration is performed.
- The immutable upstream Engine source and main branch remain unchanged.
