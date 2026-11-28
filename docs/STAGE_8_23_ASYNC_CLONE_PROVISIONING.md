# Stage 8.23 — Serialized asynchronous Clone provisioning

**Implementation status:** changes prepared for feature branch `feat/veyra-vault-product-foundation`; CI and compile verification are pending until the commit is pushed and its workflow runs complete. No physical-device certification is claimed.

## Objective

Remove synchronous virtualization Engine work from Add App and Duplicate Clone UI callbacks, preserve token-bound Clone ID reservations, and serialize Engine operations which can otherwise race one another.

## Architecture

### 1. Process-wide Engine operation queue

Added `EngineOperationQueue`, backed by one process-wide `Executors.newSingleThreadExecutor` worker.

- Synchronous Engine calls submitted through the queue run off the UI thread.
- Result callbacks are posted to the Android main thread.
- The queue is shared by Clone creation, Clone launch orchestration, location-hook synchronization, pending-reservation diagnostics, GMS state operations, Clone stop/clear requests, and single/batch uninstall.
- The executor is application-process scoped and must not be shut down by an Activity or repository.
- This is serialization within a process. It does not create a cross-process mutex for the Engine's separate virtual host processes.

### 2. Application-scoped Clone provision coordinator

Added `AsyncCloneProvisionRepository`, which owns the complete Add App / Duplicate Clone transaction using the application Context:

1. Run read-only Native ABI preflight.
2. Reject denied or unknown package metadata without reserving an ID.
3. Persistently reserve a package-scoped virtual user ID.
4. Submit Engine installation to `EngineOperationQueue`; the Engine wrapper revalidates the APK fingerprint immediately before reflection.
5. On confirmed install success, atomically commit the Clone entry and consume its exact reservation token.
6. On failed install, release the reservation only when the Engine explicitly reports `ABSENT`.
7. On registry commit failure, attempt Engine uninstall on the same shared queue and release the reservation only when uninstall confirms absence.
8. Unknown Engine state, executor rejection, cleanup failure, or persistence failure leaves the reservation blocked for the existing pending-reservation recovery screen.

The coordinator retains only application-scoped Context and does not hold an Activity reference. Closing Add App or MainActivity does not cancel an already-reserved transaction. UI callbacks are used only to display completion.

### 3. UI and existing Engine operations

- `AddAppActivity` delegates single and batch clone creation to the provision coordinator.
- `MainActivity` Duplicate Clone uses the same coordinator; the two creation paths no longer duplicate transaction code.
- Dashboard GMS queries/toggles, Clone stop/clear requests, and single/batch uninstall are submitted to the shared Engine queue.
- A Clone Registry row is still removed only after `Engine.uninstallClone` positively confirms the virtual package is absent.
- Launch and location-hook repositories no longer create separate Engine worker executors; they use the shared queue.
- Pending reservation diagnostics use the shared queue for Engine state reads and no longer own/shut down a separate executor.

## Tests

Added `scripts/test_async_clone_provision_contract.py` and updated the following existing source-contract tests:

- `test_add_app_dashboard_async_persistence_contract.py`
- `test_main_activity_clone_mutations_async_contract.py`
- `test_async_clone_launch_contract.py`
- `test_main_activity_async_spaces_contract.py`
- `test_clone_id_reservation_contract.py`
- `test_engine_contract.py`

The new contract checks the one-worker queue, preflight → reservation → install → atomic commit ordering, explicit-ABSENT-only reservation release, rollback confirmation, absence of direct Engine installation in Activity code, and shared-queue use for the Engine operations moved in this stage.

## Data safety and recovery boundaries

- No Clone package data, app-private data, account, credential, or Session data is cleared or reset by the provisioning coordinator.
- An Engine install that fails or returns an unknown state does not silently free its ID reservation.
- A failed registry commit triggers an uninstall attempt; if uninstall is not positively confirmed, the reservation remains blocked and is visible to pending-reservation diagnostics.
- If the application process dies after reserving an ID, the durable reservation remains. The current recovery screen still requires a fresh Engine state check and explicit user confirmation before release.
- Room remains inactive and opt-in; CloneStore remains the active registry.

## Validation limits

- Source-contract tests are not a substitute for Gradle compilation or Android instrumentation.
- No CI result for this Stage 8.23 change is claimed until the new commit's Push and PR runs are inspected.
- Physical-device validation remains outstanding, including the Huawei DUB-LX1 / API 27 reference device and representative ARMv7/ARM64 devices.
- Engine calls originating from separate virtual host processes remain separate process contexts; this queue does not claim cross-process mutual exclusion.

## Repository invariants

- Work only on `feat/veyra-vault-product-foundation`.
- PR #4 remains Open and Draft; do not merge.
- Do not modify `main` directly.
- Preserve existing Clone data and account/Session state.
