# Stage 2 — Security and Permission Audit

## App-lock credential storage

The previous implementation stored SHA-256 of the fixed prefix `VeyraSalt_` plus the PIN/pattern. This was fast to brute-force and used a shared fixed salt.

New credentials use a versioned PBKDF2 format:
- 120,000 iterations.
- 16-byte cryptographically random salt per credential.
- 256-bit derived key.
- PBKDF2-HMAC-SHA256 on Android API 26+.
- PBKDF2-HMAC-SHA1 on API 21–25 for provider compatibility.
- Constant-time derived-key comparison.
- Strict format/iteration bounds; malformed records fail closed.

### Existing-user migration

The verifier still recognizes the exact legacy SHA-256 format. A correct legacy PIN/pattern unlocks normally and triggers an in-place upgrade to the versioned PBKDF2 format. An incorrect secret never changes stored data. If persisting the upgraded hash fails, the verified user is still allowed to unlock and the legacy hash remains available for a later retry.

The existing SharedPreferences file and keys (`veyra_security_prefs`, `lock_mode`, `lock_hash`) are unchanged. PIN/pattern mode values are unchanged. No credential is reset during migration.

## Permission management audit

The existing permission screen reads package-requested permissions and stores values in `CloneEntry.deniedPermissions`. Repository inspection found no runtime consumer that applies those values to Android's permission manager or to the clone engine. Therefore, these values are currently metadata only.

To avoid presenting a non-functional control as enforcement:
- Existing saved flags remain untouched.
- Requested permissions remain visible.
- Checkboxes are read-only.
- Both language resources disclose that runtime blocking is not yet implemented.

A future permission-enforcement stage must identify a supported engine API, test it against the actual embedded engine version, and verify behavior per virtual user without changing Android host-app grants.

## Device Admin accuracy

The previous UI claimed that no user or app could uninstall VeyraVault. That claim was inaccurate. Android Device Admin is revocable through system settings; the user must deactivate the app's admin status before uninstalling it. The UI now explains this limitation in Persian and English. No stronger device-owner policy is claimed.

## Validation

- Standalone Java tests cover PBKDF2-HMAC-SHA256 and PBKDF2-HMAC-SHA1 formats, correct and incorrect credentials, null/malformed inputs, and legacy-hash verification/upgrade.
- CI runs the credential tests before the Android build.
- The Android build compiles the app with minSdk 21.
- Device-level verification is still required for provider availability/performance on representative Android 5–8 devices and for the actual SharedPreferences upgrade path.

## Deliberate non-goals

- No lockout or retry policy was added; that requires product decisions and careful recovery UX.
- No biometric dependency or Android Keystore migration was added.
- No attempt is made to revoke permissions granted to the host app or to modify third-party app security behavior.
- No clone lifecycle, session, or stored clone data changes.


## Upstream engine remote log transmission

A review of the pinned upstream BlackBox engine commit found a hard-coded remote log destination and crash-handler calls capable of uploading logcat/device information. This path was not adequately covered by the earlier source-only review.

The build preparation now fails closed if the expected engine files or source pattern are missing, sets the engine log destination to null, and replaces the network-capable LogSender with a no-network stub. Both source and compiled APK audits now fail if the known remote log-upload endpoint remains. This patch is applied to the pinned engine workspace before compilation; it does not rewrite clone data or session storage.

The CI build must pass the new source and binary checks before this mitigation is considered validated. Device-level behavior remains untested.
