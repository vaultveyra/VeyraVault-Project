# Stage 8.39 — Read-only AccountManager IDs in Clone identity diagnostics

Status: implementation added on the feature branch; CI validation pending.

## Purpose

Stage 8.38 added a fail-closed, numeric-ID-only AccountManager inventory API. The Settings diagnostics page still consumed only the Engine virtual-user inventory, so the AccountManager keys were not yet visible or compared in the app.

This stage connects the existing API to the read-only diagnostics page. It does not change the allocator or any Engine account data.

## What the report now compares

The diagnostics reads three sources:

1. Strict current CloneStore registry identities (package name + numeric user ID).
2. Engine's current virtual-user IDs.
3. AccountManager's numeric user-bucket map keys.

The report displays:
- cross-package Clone collisions for the same numeric user ID;
- Engine IDs with no current Clone numeric ID, and Clone IDs absent from the current Engine list;
- AccountManager keys absent from the current Engine list (historical/orphan candidates, not proven orphan records);
- AccountManager keys with no current Clone numeric ID;
- AccountManager keys whose numeric ID is used by multiple current Clone packages.

AccountManager bucket keys are never mapped to a specific package. If two Clone packages share userId 0, the report may identify numeric bucket 0 as sharing the same Engine user scope; it does not claim every app can enumerate or read every account.

## Privacy and safety boundary

- AccountManager API returns only sorted numeric keys.
- No account names/types, passwords, userData, visibility records, auth tokens, session data, cookies or app-private files are read.
- Diagnostics remains read-only and non-exported.
- If either Engine inventory is unavailable, the page shows a partial/incomplete report and never declares an all-clear state.
- The UI caps a displayed numeric-ID list at 100 entries; the heading retains the full count.
- No ID is released, reserved, remapped, deleted or automatically repaired.
- No CloneStore record, virtual package, account, credential, token, session or app-private directory is changed.
- The global monotonic allocator remains disabled.

## Tests

The Android instrumentation suite now covers:
- sorting and classification of AccountManager numeric keys;
- candidate historical IDs absent from Engine and Clone numeric inventories;
- numeric IDs shared across different Clone packages without assigning the bucket to a package;
- rejection of null, negative, duplicate and unavailable AccountManager inventories;
- immutable AccountManager report collections.

The CI source contract verifies that the Settings screen calls the ID-only Engine API and that neither the audit helper nor screen accesses account values or mutation APIs.

## Validation boundary

CI run #1437 passed on parent ff012c740ca55d93b0ccffae2bf736c644a4ccf4 before this Stage 8.39 change. That run validates Stage 8.38 and the preceding diagnostics; it does not validate this new wiring. A fresh CI run on this commit is required.

This is diagnostic visibility, not a fix for the underlying AccountManager scope mismatch and not runtime account/session isolation certification. Synthetic Android tests do not replace a physical-device test with synthetic apps/accounts. Keep sessionDataIsolation, cookieStorageIsolation, databaseIsolation and sharedPreferencesIsolation as NOT_IMPLEMENTED until end-to-end tests pass.
