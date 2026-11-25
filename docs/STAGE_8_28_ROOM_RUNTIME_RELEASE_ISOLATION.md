# Stage 8.28 — Room runtime isolation and V1 META-INF integrity

## Finding

The Stage 8.27 signed Release APK contained 49 entries under `META-INF/` that `apksigner` reported as not protected by V1 JAR signing. Two were Kotlin Coroutines ServiceLoader descriptors:

- `META-INF/services/kotlinx.coroutines.internal.MainDispatcherFactory`
- `META-INF/services/kotlinx.coroutines.CoroutineExceptionHandler`

The other entries were AndroidX `.version` markers and AGP/version-control build metadata. The pinned build workspace adds Room 2.6.1 even though Room is still an opt-in migration foundation and CloneStore remains the production source of truth.

The AndroidX Room project merged the prior `room-ktx` implementation into `room-runtime` and explicitly added Coroutines as a dependency. Consequently, packaging Room 2.6.1 in every app variant also pulled Kotlin Coroutines runtime classes and the two service descriptors into Release. See the upstream AndroidX change: https://android.googlesource.com/platform/frameworks/support/+/24d3ee6da52850f2f9499a641a4d88d9c5943e12

## Implementation

The generated workspace now scopes dependencies as follows:

- `debugImplementation room-runtime:2.6.1`: Room is packaged in Debug so Android instrumentation tests can exercise the migration foundation.
- `releaseCompileOnly room-runtime:2.6.1`: production Java sources retain the Room API on the compile classpath, but Room runtime code and its transitive Coroutines dependencies are not packaged in Release.
- `debugAnnotationProcessor room-compiler:2.6.1`: generated Room implementation code is produced only for Debug, where the instrumentation harness runs.

No production source calls `ClonePersistenceDatabaseProvider.get()`. CloneStore remains the active runtime store. The provider is intentionally dormant; enabling Room in production later requires an explicit migration stage and restoring a runtime dependency together with migration and device tests.

The workspace excludes only these non-runtime metadata patterns:

- `META-INF/*.version`
- `META-INF/com/android/build/gradle/app-metadata.properties`
- `META-INF/version-control-info.textproto`

No broad `META-INF/**` or `META-INF/services/**` exclusion is introduced. Debug keeps the Coroutines descriptors and the API-21 instrumentation test still verifies both resource contents and provider class loadability.

## Fail-closed validation

- `scripts/audit_apk.py` now rejects any non-directory `META-INF/` entry in the unsigned Release APK. This makes unexpected Java service resources or build metadata a package-audit failure rather than a signing warning.
- The isolated signing job captures both stdout and stderr from `apksigner verify` and fails if the output contains `not protected by signature`.
- V1, V2 and V3 remain mandatory. V1 is not disabled because the app's minimum API is 21.
- The existing API-34 suite and dedicated API-21 Debug smoke test continue to exercise the Debug variant, including the two required ServiceLoader resources.

## Scope and safety

This stage changes only build-time dependency scopes, precise packaging exclusions, source contracts, APK auditing, and CI signing validation. It does not alter Engine source, CloneStore behavior, Room schema/data, migration execution, VPN behavior, or user Clone data. No account, session, credential, or Clone data is read or modified by these build checks.

Validation is CI/emulator-based. API-21 x86_64 smoke coverage is not physical-device certification for ARM hardware, Huawei firmware, or native Engine virtualization.



## Stage 8.29 follow-up

Both Stage 8.28 CI runs passed API-34 and API-21 tests but the Release APK audit still found four entries: two Kotlin Coroutines ServiceLoader descriptors, AGP app metadata, and AGP VCS metadata. Stage 8.29 migrates the generated build file to AGP's current packaging DSL and disables Release VCS metadata explicitly.

The two Coroutines service descriptors are not removed. CI now records Gradle dependency insight against the actual `releaseRuntimeClasspath` for Coroutines and Room so their origin can be resolved before any release-only exclusion or dependency change is considered.

The strict Release APK audit and signing gate remain active. No final Release validation is claimed until the APK passes the metadata audit and V1/V2/V3 signature verification.
