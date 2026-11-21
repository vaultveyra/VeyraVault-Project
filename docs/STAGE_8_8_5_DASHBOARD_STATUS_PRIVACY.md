# Stage 8.8.5 — Dashboard status privacy and Device Admin availability

## Changes

- The Dashboard performs its read-only security/Engine refresh only while the app session is authenticated.
- The status card is redacted when Dashboard leaves the foreground and remains redacted if the session is locked. A fresh status read occurs after the authenticated Dashboard resumes.
- A missing Android Device Policy service is reported as unavailable, not inaccurately as Device Admin inactive.
- The existing active/inactive answer still comes from Android's actual Device Admin state when the system service is present.

## Safety

- No lock credential, session, Device Admin, Engine or Clone state is changed by the Dashboard status card.
- The visibility guard uses the existing authenticated session state; it does not unlock the app or bypass the lock screen.
- Background read cancellation/stale-generation protection remains in place.
- No permission request, administrator activation/deactivation, persistence schema, or startup behavior is changed.

## Verification

The Dashboard status contract checks authenticated-session gating, status redaction on pause, main-thread/lifecycle-safe display, and separate unavailable versus inactive Device Admin reporting. The full CI pipeline remains the acceptance gate for this stage.
