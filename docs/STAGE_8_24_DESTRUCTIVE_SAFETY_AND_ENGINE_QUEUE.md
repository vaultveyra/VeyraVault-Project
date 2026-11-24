# Stage 8.24 — Destructive-operation safeguards and serialized Engine diagnostics

## Scope

This stage hardens the existing Clone action sheet and routes diagnostic Engine reads through the
same process-wide queue used by clone provisioning, launch, GMS, stop, clear, uninstall, and
pending-reservation inspection.

## Destructive Clone actions

- Clear Data now requires an explicit confirmation dialog that explains the exact scope:
  private app data, databases, preferences, app-specific files, and the package/user-scoped
  Android/data directory. It warns that saved sign-ins and sessions may be lost.
- Single Clone uninstall now requires a separate confirmation with a data-loss warning.
- Batch uninstall has a second final confirmation after selection and lists the selected Clone
  names and Space numbers before any Engine operation is queued.
- Canceling any confirmation queues no Engine operation and performs no CloneStore mutation.
- The confirmation text explicitly states that the pinned Engine API cannot independently prove
  that every underlying data-file deletion completed. Users are advised to keep independent
  backups of important information.

## Engine result semantics

- `Engine.stopClone` and `Engine.clearCloneData` now return false for invalid identities,
  unavailable Engine core, missing supported method, or reflection failure.
- A true result means only that the Engine method was invoked without a reflection error.
  The pinned upstream stop/clear APIs do not expose a verified process-termination or complete
  file-cleanup result. The UI must not describe dispatch as verified completion.
- Uninstall remains fail-closed for registry removal: the app removes the CloneStore record only
  after the Engine explicitly reports that the package is absent. This is install-state
  confirmation, not proof of secure erasure of every data file.

## Serialized diagnostic reads

- Per-Clone compatibility reports execute through `EngineOperationQueue`.
- Host compatibility reports execute through `EngineOperationQueue`.
- Dashboard security, device-admin and Engine status reads execute through `EngineOperationQueue`.
- The diagnostic Activities no longer create private worker executors for Engine calls.
- Engine startup/lifecycle initialization in `VaultApp` remains a separate lifecycle path and is
  intentionally not moved into the runtime operation queue.

## Validation

- Added `scripts/test_stage_8_24_destructive_safety_engine_queue.py` and wired it into CI.
- CI must still validate Java compilation, Android instrumentation, source audit, unsigned APK
  packaging/audit and the isolated signing job.
- No Clear Data, Clone uninstall, app-data removal, Room migration, account/session reset or
  startup mutation is executed by this stage.
- No physical-device certification is claimed. Stage 8.25 adds build-time checks for the
  pinned Engine's data-directory deletion and reset-directory recreation; neither stage promises
  forensic secure erasure.
- Room remains inactive and opt-in only. CloneStore remains the active runtime source of truth.
- Work remains confined to `feat/veyra-vault-product-foundation`; PR #4 stays Open and Draft.
