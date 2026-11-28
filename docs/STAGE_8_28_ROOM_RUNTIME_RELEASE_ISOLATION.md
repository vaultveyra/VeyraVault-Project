# Stage 8.28 — Room runtime isolation and Release META-INF inventory

## Original finding and hypothesis

The Stage 8.27 signed Release APK contained 49 entries under `META-INF/` that the Android APK verifier reported as not protected by V1 JAR signing. Two were Kotlin Coroutines ServiceLoader descriptors:

- `META-INF/services/kotlinx.coroutines.internal.MainDispatcherFactory`
- `META-INF/services/kotlinx.coroutines.CoroutineExceptionHandler`

The other entries included AndroidX `.version` markers and AGP/version-control build metadata. At the time, Room 2.6.1 was suspected of being the primary source of the Coroutines resources. That was a useful hypothesis to investigate, but later Release dependency provenance did not support attributing the remaining descriptors solely to Room.

## Room implementation

The generated workspace scopes Room as follows:

- `debugImplementation room-runtime:2.6.1`: Room is packaged in Debug so Android instrumentation tests can exercise the migration foundation.
- `releaseCompileOnly room-runtime:2.6.1`: production Java sources retain the Room API on the compile classpath, but Room runtime code is not packaged in Release.
- `debugAnnotationProcessor room-compiler:2.6.1`: generated Room implementation code is produced only for Debug, where the instrumentation harness runs.

No production source calls `ClonePersistenceDatabaseProvider.get()`. CloneStore remains the active runtime store. The provider is intentionally dormant; enabling Room in production later requires an explicit migration stage and restoring a runtime dependency together with migration and device tests.

## Precise workspace packaging

The workspace excludes only these build metadata patterns:

- `META-INF/*.version`
- `META-INF/com/android/build/gradle/app-metadata.properties`
- `META-INF/version-control-info.textproto`

The Release VCS stamp is also disabled through AGP's `vcsInfo.include = false`. No broad `META-INF/**` or `META-INF/services/**` exclusion is introduced. The two required Coroutines descriptors remain present, and the API-21 Debug instrumentation test verifies their contents and provider class loadability.

## Stage 8.29 dependency-provenance result

On commit `1c214ffc8982994d686320125460bda001b2115e`, both Push and Pull Request CI completed the API-34 instrumentation suite, API-21 legacy smoke test, source audit, dependency inspection, and unsigned Release compilation. The package audit still failed on exactly three entries:

- `META-INF/com/android/build/gradle/app-metadata.properties`
- `META-INF/services/kotlinx.coroutines.CoroutineExceptionHandler`
- `META-INF/services/kotlinx.coroutines.internal.MainDispatcherFactory`

The VCS metadata entry was no longer present. Gradle's `releaseRuntimeClasspath` report traced `kotlinx-coroutines-android:1.6.1` through `androidx.lifecycle:lifecycle-viewmodel-savedstate:2.5.1`, `androidx.fragment:fragment:1.3.6`, and `com.google.android.material:material:1.9.0`, originating from `project :Bcore`. `kotlinx-coroutines-core:1.6.1` was part of that dependency graph. Room returned no matching dependency in `releaseRuntimeClasspath`, confirming the Room runtime isolation worked.

Therefore, the two service descriptors are required by the resolved Release dependency graph and must not be stripped. The initial Room-only attribution is superseded by the captured dependency path above.

## Stage 8.30 correction to the V1 audit model

The previous unsigned-APK audit rejected every non-directory `META-INF/` entry and described them as outside V1 coverage. That rule was too broad and conflated two different checks: the unsigned APK has not yet been signed, and the V1 JAR scheme does not cover ordinary entries under `META-INF/` even after signing. AOSP's `V1SchemeVerifier` explicitly reports those entries as warnings unless they are the manifest or signature-block files.

Stage 8.30 replaces the blanket rejection with an exact three-entry allowlist, validates both ServiceLoader provider descriptors, and rejects every unknown or duplicate `META-INF/` path. The isolated signing job permits warnings only for those exact expected entries and still requires V1, V2, and V3 verification. V2/V3 integrity verification remains mandatory because those APK signature schemes protect the APK contents beyond the V1 JAR coverage area.

References:
- AOSP apksig V1 verifier: https://android.googlesource.com/platform/tools/apksig/+/refs/heads/mirror-goog-studio-master-dev/src/main/java/com/android/apksig/internal/apk/v1/V1SchemeVerifier.java
- Android APK Signature Scheme v2 documentation: https://source.android.com/docs/security/features/apksigning/v2

## Scope and safety

This stage changes only build-time dependency scopes, precise packaging inventory rules, source contracts, and CI signing validation. The pinned Engine source is unchanged. CloneStore remains the active production persistence source; Room remains opt-in/debug-only. No user Clone data, account, session, or credential is read or modified.

Validation is CI/emulator-based. API-21 x86_64 smoke coverage is not physical-device certification for ARM hardware, Huawei firmware, or native Engine virtualization.
