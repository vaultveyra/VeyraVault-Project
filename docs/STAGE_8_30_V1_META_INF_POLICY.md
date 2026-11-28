# Stage 8.30 — Exact META-INF inventory and V1 warning policy

## Root cause

The unsigned Release package audit enumerated every non-directory path beginning with `META-INF/` and failed when that list was non-empty. This was not a signature verification: the APK was unsigned at that point, and the script did not inspect a signature manifest. It was an over-broad package inventory rule.

The Android Open Source Project's V1 verifier confirms the underlying limitation. Ordinary files under `META-INF/`—other than the JAR manifest and V1 signature files—are reported as not protected by JAR/V1 signing. The warning is part of V1 semantics, not a failure of V2/V3 APK signing.

## Exact allowlist

The Release APK may retain only these three non-directory META-INF entries:

- `META-INF/com/android/build/gradle/app-metadata.properties` — AGP-generated build provenance.
- `META-INF/services/kotlinx.coroutines.CoroutineExceptionHandler` — must declare exactly `kotlinx.coroutines.android.AndroidExceptionPreHandler`.
- `META-INF/services/kotlinx.coroutines.internal.MainDispatcherFactory` — must declare exactly `kotlinx.coroutines.android.AndroidDispatcherFactory`.

The two ServiceLoader descriptors are required by the resolved Release dependency path through Material, Fragment, and Lifecycle. The API-21 instrumentation test separately validates that the resources are discoverable and both provider classes can be loaded. The AGP metadata file is optional in the policy, but if present it is accepted only at that exact path.

Every other META-INF resource is rejected. Duplicate paths, missing service descriptors, malformed UTF-8, and unexpected provider declarations are rejected. No broad `META-INF/**` or `META-INF/services/**` exclusion is used.

## Signature verification

The isolated signing job continues to sign with V1, V2, and V3 enabled. It permits `not protected by signature` warnings only for the exact entries above; any other warning fails the job. It then requires all of these verifier results:

- `Verified using v1 scheme (JAR signing): true`
- `Verified using v2 scheme (APK Signature Scheme v2): true`
- `Verified using v3 scheme (APK Signature Scheme v3): true`

V1 remains enabled for the minimum supported Android API 21. V2/V3 verification protects the APK contents, including the ordinary META-INF resources not covered by V1's JAR-entry rules. The signed job cannot report success unless all required schemes verify and no unrecognized V1-unprotected entry is reported.

## Provenance

The Stage 8.29 Release dependency report showed:

- `kotlinx-coroutines-android:1.6.1` comes through `material:1.9.0` → `fragment:1.3.6` → `lifecycle-viewmodel-savedstate:2.5.1`.
- `kotlinx-coroutines-core:1.6.1` is part of that resolved graph.
- `androidx.room:room-runtime` is absent from `releaseRuntimeClasspath`.

Room remains Debug-only/compile-only for Release. CloneStore remains the active production persistence source.

## Validation boundary

The new policy is exercised with synthetic archive fixtures: expected entries pass, while unknown files, duplicate paths, missing service descriptors, and provider drift fail. CI must then pass the full API-34 suite, API-21 smoke test, source audit, unsigned Release package audit, and isolated signed V1/V2/V3 verification.

No physical Huawei DUB-LX1 or other ARM device has been tested by this stage. Emulator coverage does not certify native virtualization behavior on physical hardware.

## References

- AOSP V1 verifier implementation: https://android.googlesource.com/platform/tools/apksig/+/refs/heads/mirror-goog-studio-master-dev/src/main/java/com/android/apksig/internal/apk/v1/V1SchemeVerifier.java
- Android APK Signature Scheme v2: https://source.android.com/docs/security/features/apksigning/v2
