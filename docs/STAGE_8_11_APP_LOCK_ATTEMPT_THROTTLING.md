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
- At process creation, the persisted wall-clock deadline is converted once into a monotonic `SystemClock.elapsedRealtime()` deadline. The reconstructed delay is capped at 15 minutes.
- During that process lifetime, subsequent checks use only the monotonic deadline; they do not keep refreshing it from wall time. Moving the device clock backwards therefore cannot continually restart or extend an active cooldown, and moving it forwards cannot shorten the active in-process cooldown.
- After ordinary process recreation, the wall-clock deadline is used to reconstruct the remaining delay, but the reconstruction remains capped at 15 minutes. Android reboot/time-change behavior is not claimed to be tamper-proof or hardware-backed.
- Attempt metadata must contain a consistent pair: counts 0–4 require a zero deadline; counts 5 or higher require a positive deadline. Malformed or inconsistent metadata fails closed for the bounded maximum cooldown and normalizes only the attempt metadata. It does not clear or rewrite the existing credential.
- If durable preference storage fails after an incorrect attempt, an in-process 30-second fallback prevents rapid retries while that process remains alive. The fallback cannot guarantee persistence across process death when Android reports a storage failure.

## Verification

- Added deterministic Java tests for every cooldown boundary, saturation, expiry, overflow, malformed metadata, bounded wall-clock reconstruction and resistance to repeated backwards wall-clock changes within a process.
- Added Android instrumentation that verifies four unthrottled failures, the fifth-failure cooldown, rejection of a correct PIN during active cooldown, successful unlock after expiry, and exact restoration of the original security preferences and process flags.
- Extended the credential test harness to compile/run both the existing KDF migration tests and the new attempt-policy tests.
- Added a CI source contract requiring lockout-before-derivation ordering, reset behavior, persisted metadata consistency, one-time monotonic reconstruction, and localized feedback.

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

## Instrumentation fixture compatibility

- The pre-existing app-lock lifecycle instrumentation snapshots and restores both attempt-throttling preference keys and both in-memory monotonic/counter fields.
- The process-isolation instrumentation fixture now snapshots and restores the entire original credential preference map as well as the host process unlock and throttle state.
- These fixtures preserve pre-test state exactly, including the case where attempt-throttling keys did not exist before the test. The first CI failures were cleanup assertions in these older fixtures, not failures in the new attempt-throttling behavior assertions.
- CI must pass both Push and PR runs on the final commit before this stage's automated verification is considered complete.
