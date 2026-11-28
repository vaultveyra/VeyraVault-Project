# Stage 8.45 — Complete profile editor discoverability and settings-path clarity

Status: implementation committed; CI validation pending.

## Scope

This stage improves the two entry points for the canonical 104-field profile registry without changing profile precedence, persistence schemas, runtime adapters, Clone identity, Engine behavior, or account/session data.

## Changes

- Added an in-page search field to the shared Global / per-Clone profile editor.
- Search matches stable field key, human-readable field label, category (including the Persian category label), validation rule, capability, adapter identifier, API support, privacy class, readback method, note, and unsupported reason.
- Category headings are hidden when no field in that category matches. A localized empty state and visible Showing X of Y fields / Persian equivalent are provided.
- Localized the profile status summary so Persian users can read Applied, Stored Only, Unsupported, Not Tested, Failed, and Not Applicable counts.
- Clarified Settings navigation: Complete Environment Profile (All Fields) is the single entry point for the full Global registry. Advanced Location & Legacy Controls is explicitly limited to Master Location and legacy-compatible controls.
- Added contract assertions for search behavior, Persian category search, localized status summary, and the separation between the full editor and legacy controls.

## Safety and compatibility

- No profile field IDs, types, validation rules, capability classifications, safe defaults, or resolver precedence changed.
- No Clone or Global stored values were migrated, cleared, or overwritten.
- No runtime Engine code, Android API hooks, network routing, hardware identifiers, accounts, credentials, tokens, sessions, cookies, or app data were modified.
- Restricted, service-owned, and observed-only fields remain read-only.
- A saved profile value is not reported as applied without a verified adapter and readback.
- Existing Clone editor and Settings entry points continue to open the same registry-driven editor.
- Legacy location controls remain available and separately labeled; this stage does not retire or migrate their persistence.

## Validation boundary

The existing CI contract scripts/test_profile_document_editor_contract.py now asserts search wiring and Settings navigation clarity. A green CI run validates source/build/instrumentation contracts; it does not prove every editable profile field is applied inside every third-party cloned app. Physical-device and per-field runtime readback remain separate acceptance gates.
