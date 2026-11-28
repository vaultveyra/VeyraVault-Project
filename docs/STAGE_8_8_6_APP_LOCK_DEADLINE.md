# Stage 8.8.6 — Deterministic App Lock Deadline

## Change

Extract the host app-lock timeout conversion and elapsed-realtime deadline math into `AppLockDeadline`, a production Java class with no Android dependency.

The lifecycle controller delegates timeout conversion, deadline creation, expiration checks and remaining-time calculation to this helper. Existing behavior is retained: the Immediate option uses a 250 ms Activity-transition grace; 30 seconds, 1 minute and 5 minutes retain their exact durations.

## Safety and correctness

- Uses Android elapsed-realtime values supplied by the lifecycle controller, so elapsed deep-sleep time is included.
- Treats an absent deadline as not expired.
- Treats exact deadline equality as expired.
- Fails unsupported timeout values closed to the Immediate behavior.
- Saturates deadline addition at `Long.MAX_VALUE` rather than overflowing.
- Keeps the Security Settings timeout constants connected to the helper's canonical values.
- Does not modify credential, session, clone, Room or Engine data.

## Verification

- A CI step compiles and executes the actual production Java helper with `javac`, covering exact timeout durations, before/at/after deadline boundaries, simulated deep-sleep elapsed time, invalid values, missing deadlines and overflow.
- An Android instrumentation test exercises the same production class.
- The lifecycle source contract asserts the controller delegates deadline behavior to the helper.
