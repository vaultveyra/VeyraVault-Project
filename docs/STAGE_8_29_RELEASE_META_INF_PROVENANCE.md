# Stage 8.29 — Release META-INF provenance and AGP metadata controls

## Stage 8.28 context

Stage 8.28 isolated Room runtime and code generation from Release. It also replaced broad packaging removal with targeted exclusions. The follow-up investigation in this stage uses Gradle's resolved `releaseRuntimeClasspath` rather than relying on a dependency's published metadata in isolation.

## Changes

- Configure Release `vcsInfo.include = false` through the AGP BuildType VcsInfo API.
- Replace deprecated `packagingOptions` configuration with AGP's `packaging.resources.excludes` DSL.
- Keep exact exclusions for known build metadata only; no broad `META-INF/**` or `META-INF/services/**` removal.
- Preserve API-21 Debug instrumentation that validates the two Coroutines service descriptors and provider class loadability.
- Add CI Gradle dependency insight for `kotlinx-coroutines-android`, `kotlinx-coroutines-core`, and `androidx.room:room-runtime` against `releaseRuntimeClasspath`.
- Keep APK inventory and signing checks fail-closed.

## Stage 8.29 CI findings

Both Push run `45657908733` and Pull Request run `45657920735`, for commit `1c214ffc8982994d686320125460bda001b2115e`, completed the API-34 instrumentation suite, API-21 legacy smoke test, source audit, dependency inspection, and unsigned Release compilation. Both stopped at the APK package audit with exactly three entries remaining:

- `META-INF/com/android/build/gradle/app-metadata.properties`
- `META-INF/services/kotlinx.coroutines.CoroutineExceptionHandler`
- `META-INF/services/kotlinx.coroutines.internal.MainDispatcherFactory`

The prior `META-INF/version-control-info.textproto` entry was removed by disabling Release VCS metadata. Room did not appear in `releaseRuntimeClasspath`. The Coroutines path was:

```
project :Bcore
└─ com.google.android.material:material:1.9.0
   └─ androidx.fragment:fragment:1.3.6
      └─ androidx.lifecycle:lifecycle-viewmodel-savedstate:2.5.1
         └─ org.jetbrains.kotlinx:kotlinx-coroutines-android:1.6.1
            └─ org.jetbrains.kotlinx:kotlinx-coroutines-core:1.6.1
```

This confirms that the two service descriptors are part of the current Release runtime graph and should be preserved. The earlier hypothesis that Room was their sole source was not supported by this resolved configuration.

## V1 audit correction carried into Stage 8.30

The Stage 8.29 builds exposed a flaw in the pre-sign audit: it rejected every non-directory `META-INF/` file in an unsigned APK and called it a V1 integrity failure. AOSP's V1 verifier intentionally treats ordinary `META-INF/` files as outside JAR/V1 coverage and emits a warning for them. That warning is not evidence that the whole APK is unprotected: V2/V3 verify the APK signing block and full APK content.

Stage 8.30 therefore uses a strict exact-path allowlist for the AGP provenance file and the two required Coroutines service descriptors, validates the provider contents, and rejects any unexpected or duplicate `META-INF/` entry. The signer accepts only warnings for those exact paths; V1 remains enabled and required, and V2/V3 remain mandatory. This corrects the verification model without removing runtime resources or weakening the unknown-entry gate.

## Scope and safety

No broad resource exclusion is added. The pinned Engine source, CloneStore runtime behavior, Room schema/data, user Clone data, accounts, credentials, and sessions are not modified. Physical Huawei DUB-LX1/ARM hardware validation remains outstanding; emulator results are not device certification.
