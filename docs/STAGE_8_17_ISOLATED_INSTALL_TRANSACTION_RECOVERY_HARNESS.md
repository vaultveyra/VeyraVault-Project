# Stage 8.17 — Isolated Install Transaction Recovery Harness

**Status:** Isolated filesystem model implemented and CI test step passed. Production Engine integration remains blocked.
**Base design:** \`docs/STAGE_8_16_TRANSACTION_JOURNAL_STAGING_COMMIT_ROLLBACK_DESIGN.md\`
**Implementation commit:** \`9d23d153883ff9a210cdd8b386170ad49276b404\`
**Audited Engine:** \`ALEX5402/NewBlackbox@89b59836c66f173756a4ae258cf379a957649820\`

## 1. Scope

Stage 8.17 implements an isolated Python filesystem model of the Stage 8.16 transaction protocol. It is intended to test journal durability boundaries, directory publication, rollback, and startup recovery before any production Engine source is changed.

The harness is deliberately separate from Android runtime code. It does not install APKs, call BlackBox APIs, alter CloneStore, or operate on the user's real app data.

## 2. Implemented harness

File:

\`scripts/test_stage_8_17_install_transaction_recovery.py\`

The model creates isolated temporary roots with separate locations for:

- active package generation;
- transaction journal and staging directory;
- previous package backup;
- staged and previous per-user native-library directory;
- virtual-user files and shared preferences;
- device-protected and external virtual-user data;
- host-side CloneStore registry and pending-reservation journal.

Journal files use a sibling temporary file, file flush/fsync, atomic replacement, and parent-directory fsync in the Linux test environment. Package and user-library directory publication uses same-filesystem \`os.replace\` in the isolated temporary root.

The journal is versioned and validates its exact schema, transaction UUID, package name, user ID, phase, and user-state list. Recovery derives filesystem locations from validated identity fields rather than accepting arbitrary paths from the journal.

## 3. State machine exercised

The model exercises the following states:

1. \`PREPARING\`
2. \`STAGED_VALIDATED\`
3. \`OLD_GENERATION_BACKED_UP\`
4. \`OLD_USER_LIB_BACKED_UP\`
5. \`USER_LIB_PUBLISHED\`
6. \`NEW_GENERATION_PUBLISHED\`
7. \`PACKAGE_METADATA_COMMITTED\`
8. \`COMPLETE\`

Recovery is deterministic and fail-closed:

- An incomplete transaction is rolled back to its last-known-good package and user-library generation.
- A transaction durably marked \`COMPLETE\` is verified before backup cleanup.
- A corrupt, unsupported, contradictory, or path-tampered journal stops recovery without deleting active, staged, or backup candidates.
- A missing required backup does not authorize deleting or guessing at the remaining generation.
- Recovery can be repeated after a partial rollback because restored generations are checked against their recorded identity and digest.

## 4. Test coverage

The suite contains seven unittest groups:

- successful replacement with preservation of installed-user state and unrelated data;
- process-death injection at 16 journal, staging, rename, metadata, and completion boundaries;
- fresh-install rollback without an existing package generation;
- invalid package-name rejection before filesystem mutation;
- corrupt-journal fail-closed behavior while active and backup generations coexist;
- unsupported journal schema and package-path tampering;
- missing-backup recovery failure without destructive guessing.

The preservation assertions cover:

- previous package generation and per-user installed-state list;
- existing per-user files and shared preferences;
- device-protected data;
- external virtual-user data;
- host CloneStore registry;
- pending reservation journal.

The isolated user-library tests also verify that a partially published library is removed and the previous library is restored on rollback.

## 5. Production-source blocker audit

After workspace preparation, the same CI step inspects the pinned Engine source and requires explicit re-audit if the known control flow changes.

At this commit the audit confirms these hazards are still present:

1. \`BPackageSettings.save()\` returns a boolean failure result, but the install caller ignores it.
2. \`Settings.updatePackageLP()\` still deletes the package directory from its catch path rather than quarantining it for recovery.
3. \`CreatePackageExecutor\` still deletes the active package directory before replacement publication is complete.

The script prints these as **production integration blockers**. The test step passing means the isolated model behaved as specified and the blockers were detected; it does not mean the production installer has been made transactional.

## 6. CI wiring and evidence

The workflow now runs:

\`python3 scripts/test_stage_8_17_install_transaction_recovery.py\`

after \`Prepare build workspace\` and before the pinned Engine ABI source-contract test. This placement ensures the audit sees the exact generated, pinned Engine source used by the build.

For commit \`9d23d153883ff9a210cdd8b386170ad49276b404\`:

- Push workflow run #1045: Stage 8.17 harness step completed successfully.
- Pull Request workflow run #1044: Stage 8.17 harness step completed successfully.
- The Stage 8.13 ABI source-contract step also completed successfully in both runs.
- At the time this report was prepared, the overall workflow jobs were still executing the Android emulator instrumentation step; no overall workflow success is claimed here.

Recent emulator failures on earlier commits included \`StorageManager.getVolumes()\` returning through a null service and \`Can't find service: package\` during \`install-create\`. Those failures occurred before instrumentation assertions could execute. They are tracked as CI emulator infrastructure instability, not silently reclassified as application test passes.

## 7. Validation limits

- The harness exercises Python filesystem semantics on the hosted Linux runner only.
- It does not prove Android \`AtomicFile\`, \`Os.rename\`, SELinux, app-private directory permissions, directory fsync, or power-loss behavior across API levels.
- It does not prove the pinned Engine can restore package state after real Android process death.
- It does not test real APK parsing, certificate lineage, ABI loading, split APK handling, or Clone Activity launch.
- No physical device was connected or tested. The Huawei Y7 2019 / DUB-LX1 Android 8.1 profile remains the first required device validation target.

## 8. Stage 8.17 decision

**Decision:** the isolated transaction state machine and failure-injection harness are implemented and wired into CI. They are a prerequisite for runtime integration, not a substitute for it.

No production Engine or VeyraVault runtime code was modified. No install flags, ABI filters, Engine pin, CloneStore schema, reservations, SharedPreferences, Room behavior, account/session data, virtual-user data, signing configuration, or \`main\` branch content was changed.

PR #4 remains open and Draft. It must not be merged as part of this stage.

## 9. Next stage

Stage 8.18 should build a narrow adapter/contract test around the actual pinned Engine install path. It must specifically prove that a failed \`BPackageSettings.save()\` cannot return success, that package scanning quarantines rather than deletes an uncertain generation, and that the current \`FLAG_SYSTEM\` source-path behavior is preserved. Until those contracts can be tested without destructive side effects, production installer integration remains blocked.
