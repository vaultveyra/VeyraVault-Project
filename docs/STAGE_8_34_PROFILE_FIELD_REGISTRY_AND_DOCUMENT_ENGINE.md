# Stage 8.34 — Canonical profile field registry and typed document resolver

Status: implementation foundation added; persistence/UI/runtime adoption is separate and not claimed complete.

## What this stage adds

- A single registry for 44 environment and identity fields, including value type, scope, capability boundary and explanatory note.
- A typed ProfileDocument that accepts only registered, valid profile inputs and rejects restricted hardware identifiers and service-owned identity data.
- A field-by-field resolver implementing Clone override → Global profile → explicit Safe Isolated Default. It never reads Android host configuration.
- Separate source and application status. A stored value for a supported field remains NOT_TESTED until a verified runtime adapter promotes it to APPLIED.
- STORED_ONLY for local preference metadata and UNSUPPORTED for fields requiring an absent network provider or restricted platform/service-owned data.
- Contract tests for precedence, Clone independence, validation, restricted-field rejection and status promotion.

## Capability boundary in this commit

- PROCESS_SCOPED: Locale and time zone have an existing process-level applier. This new generic resolver still reports NOT_TESTED; existing lifecycle integration remains the current runtime path.
- ENGINE_SCOPED: location enablement and coordinates have package/user-scoped Engine integration, subject to runtime/device readback.
- LOCAL_PREFERENCE_ONLY: region/currency/format/unit values can be represented as preferences, but are not yet applied to third-party app APIs.
- NETWORK_PROVIDER_REQUIRED: route and DNS controls require a real VeyraVault-owned network provider and leak testing. Public IP is observed output, not a profile input.
- PLATFORM_RESTRICTED / SERVICE_OWNED: hardware identifiers, phone/account identity and integrity verdicts are not editable profile inputs.
- NOT_IMPLEMENTED: values may be modeled for future adapters but must remain STORED_ONLY, never reported as applied.

## Not included / next work

This stage does not yet migrate the existing ProfileStore JSON schema, connect the new document model to provider IPC, update Global/Clone settings screens, or add runtime adapters for remaining fields. Existing five-field runtime profile storage and lifecycle application remain authoritative until those separately tested stages land. No CloneStore, Clone identity, app-private data, account/session data or main-branch state is changed.
