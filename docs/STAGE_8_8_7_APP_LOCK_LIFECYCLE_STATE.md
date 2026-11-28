# Stage 8.8.7 — Deterministic App Lock Activity Lifecycle State

## Scope
Extract the host-process Activity foreground/background counter and deadline transition state into a pure-Java production class. Android lifecycle callbacks remain in AppLockLifecycleController and continue to own Handler scheduling and SecurityManager calls.

## Behavior covered
- The app is considered backgrounded only after the final started Activity stops.
- Returning before the deadline clears it without locking.
- Returning at or after the deadline requests a session lock.
- Multiple started Activities are counted independently.
- Configuration recreation clears the pending background deadline and does not lock.
- When app lock is disabled, a return cannot trigger a lock.

## Verification
scripts/test_app_lock_lifecycle_state_contract.py compiles the actual production AppLockDeadline.java and AppLockLifecycleState.java with javac, then runs deterministic transition cases. The existing lifecycle source contract verifies Android callback wiring, main-process-only registration, configuration-change handling, and authenticated lock routing.

## Safety boundaries
- No credential format, PIN/Pattern hashing, or credential preference is changed.
- The controller remains registered only in the main host process.
- No clone process or Engine lifecycle behavior is changed.
- PR #4 remains open and Draft; main is not modified.
