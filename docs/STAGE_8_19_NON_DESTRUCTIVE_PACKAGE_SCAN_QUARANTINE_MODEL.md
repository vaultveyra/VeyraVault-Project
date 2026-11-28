# Stage 8.19 — Non-Destructive Package Scan Quarantine Model

**Status:** Isolated quarantine model and source blocker audit implemented. Stage 8.19 CI step passed on both Push and Pull Request runs for commit \`d031eb78f9802e46802b01bb4c4bfd9322f9d084\`. The overall Android Emulator workflow was still running when this report was prepared.
**Base design:** \`docs/STAGE_8_16_TRANSACTION_JOURNAL_STAGING_COMMIT_ROLLBACK_DESIGN.md\`
**Prior recovery harness:** \`scripts/test_stage_8_17_install_transaction_recovery.py\`
**Pinned Engine:** \`ALEX5402/NewBlackbox@89b59836c66f173756a4ae258cf379a957649820\`

## 1. Confirmed production scanner hazard

The pinned Engine's \`Settings.updatePackageLP(File app)\` currently reads and unmarshals \`package.conf\`, reconstructs \`BPackageSettings\`, and updates the in-memory package map.

Its catch path for a read, parse, reconstruction, or related exception currently:

1. deletes the entire package directory;
2. removes the package from the in-memory package map;
3. kills package processes; and
4. emits an uninstall notification.

The scanner does not distinguish a transient read/storage error from a permanently malformed metadata file before deleting the package directory. This is a source-level finding confirmed by Stage 8.18 and the Stage 8.19 production-source blocker audit.

**No production scanner code was changed in Stage 8.19.**

## 2. Quarantine policy modeled

The new isolated model uses a **logical recovery-required marker**, not a directory move and not deletion.

The marker is stored outside the active package directory, under a dedicated reserved recovery-record root. It includes only bounded, non-sensitive state:

- schema version;
- package name;
- status \`RECOVERY_REQUIRED\`;
- a fixed reason code; and
- the scanner phase.

The model distinguishes unreadable metadata, malformed metadata, and invalid metadata schema. It deliberately does not persist raw exception text or arbitrary filesystem paths.

When scanning encounters uncertain metadata, the model:

- leaves the active package directory and its contents in place;
- keeps previously loaded package state and component-resolver state unchanged, when available;
- records recovery-required state outside the package directory;
- suppresses uninstall notifications;
- blocks new Clone launches for the affected package; and
- returns an explicit non-success status.

A fresh process with no in-memory package state retains the files and records recovery-required status; it does not manufacture an installed package record from invalid metadata.

A later scan may clear the recovery marker and allow launches only after the metadata is readable, schema-validated, identity-matched, and the recovery marker has been safely reconciled.

## 3. Fail-closed path and marker validation

The model also rejects or blocks:

- invalid package names and package-path traversal;
- symbolic links in the app root or package directory;
- a symbolic link at \`package.conf\`;
- a symbolic link at the recovery root, records root, or package recovery record;
- corrupt or unsupported recovery-marker schema;
- recovery-marker write failure;
- recovery-marker clear failure; and
- missing or unreadable \`package.conf\`.

The default metadata reader uses \`O_NOFOLLOW\` where the test host supports it and verifies that the opened object is a regular file. This validates the Linux test model only; Android-specific file-opening and filesystem semantics still require API-level verification.

If persisting a recovery marker fails, the model keeps a process-local launch block and preserves the prior in-memory/resolver state. The malformed or unreadable metadata remains on disk so startup scanning can retry and fail closed again after process death.

## 4. Implemented tests

File:

\`scripts/test_stage_8_19_package_scan_quarantine.py\`

The isolated suite currently contains 11 unittest groups covering:

1. unreadable metadata with old in-memory and resolver state preserved;
2. malformed metadata retained without uninstall notification;
3. successful re-scan clears a valid recovery marker and re-opens the launch gate;
4. startup scan with no in-memory state preserves package files and marks recovery required;
5. recovery-marker write failure preserves the package and blocks launch;
6. invalid/unknown recovery-marker schema fails closed;
7. invalid package path and package-directory symlink rejection;
8. package metadata symlink rejection without following its target;
9. recovery-record symlink rejection without following its target;
10. recovery-root symlink rejection; and
11. missing metadata preservation without deleting the package directory.

Preservation fixtures cover package code and neighbouring files, per-user virtual data, device-protected data, external virtual data, host CloneStore registry, and pending reservation journal.

The model checks prior resolver and in-memory state rather than deleting it on an uncertain scan. It also asserts that a package in recovery-required state cannot launch, even if an older in-memory entry remains available for diagnostics and recovery.

## 5. Production-source blocker audit

After workspace preparation, the CI step reads the pinned Engine's generated \`Settings.java\` and verifies that the known destructive catch path remains visible for review.

The audit deliberately reports:

- production Engine scanner integration is **BLOCKED**;
- current scan catch still deletes the package directory; and
- the isolated quarantine model is **not wired** into production Engine.

A passing Stage 8.19 test therefore means the isolated model passes its test cases and the production blocker is detected. It does not mean the production Engine scanner has been fixed.

## 6. CI wiring and evidence

The workflow runs:

\`python3 scripts/test_stage_8_19_package_scan_quarantine.py\`

after \`Prepare build workspace\` and after the Stage 8.18 source-level install failure audit, before the ABI source contract and Android Emulator tests.

For commit \`d031eb78f9802e46802b01bb4c4bfd9322f9d084\`:

- Push run #1065: Stage 8.17, Stage 8.18, Stage 8.19, and Stage 8.13 ABI source-contract steps completed successfully.
- Pull Request run #1066: the same four source-contract steps completed successfully.
- At report time, the Android Emulator instrumentation step was still marked \`in_progress\` in both runs. No final overall workflow success is claimed here.
- The earlier emulator infrastructure failures on other commits included Android package-manager service errors during test APK installation. Those failures are not reclassified as application assertion failures.

Run links:

- Push #1065: https://github.com/vaultveyra/VeyraVault-Project/actions/runs/45319410906
- Pull Request #1066: https://github.com/vaultveyra/VeyraVault-Project/actions/runs/45319416019

## 7. Validation limits

- The model executes on the hosted Linux runner, not inside Android.
- It does not prove Android \`AtomicFile\`, \`Parcel\`, \`Os.rename\`, file descriptor semantics, SELinux permissions, or storage durability.
- It does not patch or run the pinned Engine scanner.
- It does not prove a real Clone remains launchable after recovery; it explicitly blocks new launches while metadata is uncertain.
- It does not test a physical ARM device or the Huawei Y7 2019 / DUB-LX1 reference handset.
- No real CloneStore, reservation, virtual-user data, account/session data, or user files were touched.

## 8. Stage 8.19 decision

**Decision:** accept the logical-quarantine policy as the required safe scanner behavior to implement and test in a future runtime patch. Do not modify the pinned Engine scanner in this stage.

No runtime Java, Engine source, Engine pin, install flags, ABI filters, CloneStore schema, reservations, SharedPreferences, Room behavior, account/session storage, virtual-user data, signing configuration, or \`main\` branch content was changed.

PR #4 remains open and Draft, and must not be merged as part of this stage.

## 9. Next stage

Stage 8.20 should harden the build-time Engine source identity path before any runtime Engine patch is introduced. The workspace preparation script has a local \`engine_source\` bundle branch that currently copies the directory without verifying its Git origin, pinned HEAD, or clean working tree. The normal CI path clones and checks out the immutable Engine commit, but the optional bundle path must be brought under the same identity gate.

After that, Stage 8.21 can design a narrowly scoped Engine scanner/metadata publication patch, with fault-injection tests that prove:

- save failure cannot become install success;
- scanner failure cannot delete a package directory;
- old package and resolver state remain recoverable;
- launches remain blocked while recovery is required; and
- successful recovery is required before clearing the marker or emitting an installed state.
