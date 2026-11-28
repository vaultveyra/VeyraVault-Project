# Source Audit Hardening — Forbidden Endpoint Detection

## Finding
The source audit referenced `FORBIDDEN_ENDPOINTS` without defining it. The lookup was inside a broad `except Exception` block, so the resulting `NameError` was silently swallowed for each source file. The audit could therefore finish successfully without performing its forbidden-endpoint check.

## Correction
- Define the forbidden upstream remote log host explicitly as `logs-sender-api.vercel.app`, matching the compiled-APK audit.
- Perform a case-insensitive source scan for the host.
- Limit error handling to file I/O errors and fail the audit when a source file cannot be read; programming errors are no longer silently ignored.
- Add a regression test proving clean source passes and a case-variant forbidden endpoint fails.
- Run the regression test in CI before the full source audit.

## Validation boundary
The previous Stage 8.8.7 run completed 66/66 Android instrumentation tests and built/audited an unsigned APK. However, its source audit result did not reliably prove source-level forbidden-host detection. The new regression test and a fresh CI run are required before treating that specific source-audit control as verified.

## Scope
No Android runtime behavior, credentials, clone state, Engine integration, Room activation, or persistence source-of-truth behavior is changed. PR #4 remains open and Draft; `main` is not modified.
