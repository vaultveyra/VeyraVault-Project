# Stage 8.25 — Pinned Engine cleanup failure semantics

## Problem found in the immutable upstream source

At pinned Engine commit `89b59836c66f173756a4ae258cf379a957649820`:

- `RemoveUserExecutor` discarded the return values from `FileUtils.deleteDir` and always returned success.
- `RemoveAppExecutor` did the same for the shared APK directory.
- `CreateUserExecutor` did not verify removal of its old library directory or recreation of required data directories.
- `BPackageManagerService.uninstallPackageAsUser` ignored a failed installer result and continued removing package/user metadata.
- `BPackageManagerService.uninstallPackage(String)` continued and then removed package metadata even if an individual cleanup failed.
- `BPackageManagerService.clearPackage` discarded the installer result while exposing a void API.

An Engine query reporting a package absent was therefore insufficient to prove that the target directories had been removed.

## Build-time hardening

The upstream Git pin and repository identity are unchanged. After verifying the exact clean Engine checkout, `prepare_workspace.py` applies a strict, idempotent patch only to the ephemeral build workspace:

- User-scoped internal, Device-Encrypted, Android/data, and Android/obb roots must be absent after deletion; otherwise the executor returns failure or propagates the filesystem error.
- Before recursive deletion, the Engine rejects a symlinked virtual root itself, verifies canonical containment beneath that root, and rejects symlinked package/user ancestors. Inspection failures stop cleanup before traversal.
- `CreateUserExecutor` applies the same root/containment/symlink checks before deleting the old data-library directory and prevalidates every reset target before creating any replacement directory. Symlink aliases are rejected even when they resolve back to the expected root.
- The shared APK directory must be absent before uninstall can succeed.
- Clear Data checks removal of the previous data-library directory and confirms that all required replacement directories, including the package/user-scoped OBB directory, exist.
- Uninstall removes per-user data before deleting the shared APK directory.
- A nonzero per-user cleanup result returns before package/user install metadata is removed.
- Bulk uninstall likewise preserves package metadata when any user cleanup reports failure.
- Clear Data converts nonzero cleanup results to an exception, so the host wrapper returns failure instead of a false success.

The original pinned source is still verified before the VeyraVault transformation. An unexpected source layout fails the build rather than receiving a speculative patch.

## User-facing behavior

- Clear Data warns that a failed reset may have partially removed data; the user must inspect the Clone before retrying.
- A successful reset message means the hardened Engine path returned normally after its directory checks; it is not a forensic secure-erasure guarantee.
- Failed uninstall keeps the CloneStore entry because the Engine still reports the package installed. The message warns that some files may already have been removed.

## Validation

- `scripts/test_stage_8_25_engine_cleanup_failure_semantics.py` tests the exact transformation against isolated temporary source fixtures, including idempotence and fail-closed behavior on source drift.
- CI still performs the full Java/Android build, instrumentation, source audit, APK audit and isolated signing stages.
- No user Clone, app-data directory, account, session, or credential is touched by the fixture test.
- No Room activation, migration or cutover is performed.
- No physical-device certification is claimed.
- Work remains on `feat/veyra-vault-product-foundation`; PR #4 remains Open and Draft.


## Stage 8.26 — Residual data and OBB-aware absence checks

- The pinned Engine defines a package/user-scoped `Android/obb/<package>` path. Although no active caller was found in the audited pinned source, it is now included conservatively in Clear Data/Uninstall cleanup and the reset directory set.
- `Engine.getCloneInstallState` returns `UNKNOWN`, not `ABSENT`, when the Engine says a package is not installed but any package/user-scoped internal, Device-Encrypted, Android/data, or Android/obb directory remains or cannot be safely inspected.
- Failed-install rollback and manual pending-reservation release already depend on `getCloneInstallState`; the new guard prevents ID release when orphaned package/user data remains.
- The shared package APK directory is deliberately excluded from the per-user data check because another Clone user may legitimately retain the same package binary.
- Filesystem roots must be readable and must not themselves be symlinks; canonical paths must remain beneath the expected virtual root, and symlink escapes or inspection errors fail closed. The build-time `CreateUserExecutor` reset path now enforces the same containment checks before its library deletion and directory creation. Diagnostics never delete orphan data.
- Uninstall is confirmed only when the Engine reports the package absent and all four package/user data roots are confirmed absent.
