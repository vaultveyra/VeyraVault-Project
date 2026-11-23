# Stage 8.11 — App-lock failed-attempt throttling

## Scope and source findings

- The existing PIN/Pattern verifier uses a versioned PBKDF2 credential format and upgrades the legacy fixed-prefix SHA-256 hash only after a successful verification.
- Before this stage, `verifyCredential` had no persisted failed-attempt count or cooldown. Repeated guesses could be submitted without an application-level delay.
- This stage adds a bounded local backoff for the host app-lock credential only. It does not affect virtual app credentials, Clone launch, account/session state, Engine install state or CloneStore.

## Policy

- The first four incorrect PIN/Pattern submissions are accepted without a cooldown.
- The fifth incorrect submission starts a 30-second cooldown.
- The sixth, seventh and subsequent incorrect submissions after each expired cooldown start 1-minute, 5-minute and maximum 15-minute cooldowns respectively.
- Repeated calls during an active cooldown do not derive the PIN/Pattern hash and do not increase the failure count.
- A successful credential verification resets the failed-attempt count and deadline. Setting a new credential or disabling App Lock also resets both values.
- The lockout never becomes permanent. Once the current maximum cooldown expires, the user can try again.
- Cooldown UI feedback is shown in Persian and English. PIN input is cleared after an unsuccessful verification.

## Persistence and timing

- Only two non-secret integers/timestamps are added to the existing private `veyra_security_prefs`: failed-attempt count and lockout-until wall-clock milliseconds.
- Both values are committed together. Credential hash and lock mode keys remain unchanged.
- A monotonic `SystemClock.elapsedRealtime()` companion is maintained while the host process is alive so a wall-clock adjustment cannot shorten an active cooldown in that process.
- On process recreation, the persisted wall-clock deadline reconstructs the remaining cooldown. Android reboot/time-change behavior still depends on the device wall clock; this is not claimed as tamper-proof hardware-backed rate limiting.
- If attempt metadata is malformed, the code fails closed for the bounded maximum cooldown and normalizes only the attempt metadata. It does not clear or rewrite the existing credential.
- If durable preference storage fails after an incorrect attempt, an in-process 30-second fallback prevents rapid retries while that process remains alive. The fallback cannot guarantee persistence across process death when Android reports a storage failure.

## Verification

- Added deterministic Java tests for every cooldown boundary, saturation, expiry and overflow.
- Added Android instrumentation that verifies four unthrottled failures, the fifth-failure cooldown, rejection of a correct PIN during active cooldown, successful unlock after expiry, and exact restoration of the original security preferences and process flags.
- Extended the credential test harness to compile/run both the existing KDF migration tests and the new attempt-policy tests.
- Added a CI source contract requiring lockout-before-derivation ordering, reset behavior, persisted metadata, and localized feedback.

## Non-destructive invariants

- No existing Clone records, reservations, package/user IDs, virtual app data, account/session contents or profile values are modified.
- Legacy credential hash remains verifiable; migration still occurs only after correct authentication.
- The existing credential preference keys and KDF format remain unchanged.
- No new permission, exported component, network API or server dependency is added.
- PR #4 remains Open and Draft; `main` is not modified.

## Limitations

- This is application-level rate limiting, not Android Keystore-enforced or hardware-backed throttling.
- It does not replace device-level authentication or prevent a privileged attacker from modifying private app data on a compromised device.
- Physical-device usability and persistence behavior across reboot/OEM process management remain to be validated.
