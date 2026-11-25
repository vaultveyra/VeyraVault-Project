# Stage 8.29 — Release META-INF provenance and AGP metadata controls

## Stage 8.28 verification result

Both Push and Pull Request CI on commit `6d6093c6fb5e3a2f4cd4177346eb069f627887df` reached the Release packaging audit and failed on the same four entries. Before that point, both runs passed the Stage 8.28 contract, API-34 Android instrumentation, API-21 minimum-API smoke tests, source audit, and unsigned Release compilation.

The exact Release APK audit findings were:

- `META-INF/com/android/build/gradle/app-metadata.properties`
- `META-INF/version-control-info.textproto`
- `META-INF/services/kotlinx.coroutines.CoroutineExceptionHandler`
- `META-INF/services/kotlinx.coroutines.internal.MainDispatcherFactory`

The earlier explicit exclusions removed AndroidX `.version` entries, but did not remove these four entries.

## Changes in this stage

- Configure Release `vcsInfo.include = false` through the AGP BuildType VcsInfo API.
- Replace deprecated `packagingOptions` configuration with AGP's `packaging.resources.excludes` DSL.
- Keep exact exclusions for known build metadata only; no broad `META-INF/**` or `META-INF/services/**` removal.
- Preserve API-21 Debug instrumentation that validates the two Coroutines service descriptors and provider class loadability.
- Add CI Gradle dependency insight for `kotlinx-coroutines-android`, `kotlinx-coroutines-core`, and `androidx.room:room-runtime` against `releaseRuntimeClasspath`.
- Keep the Release APK audit and signer warning gate fail-closed.

## Coroutines investigation policy

The service descriptor resources are not excluded. The precise transitive dependency path in the generated Release variant must first be captured from Gradle's resolved configuration. If a runtime dependency is required by Release, preserve its runtime behavior; if it is only test/debug infrastructure, isolate that dependency in its Gradle configuration rather than deleting resources after packaging.

## Validation gate

The unsigned Release APK must pass the exact META-INF inventory audit. The signed APK must verify V1, V2 and V3 with minimum SDK 21 and produce no `not protected by signature` warnings. API-21 and API-34 tests must remain green. A successful compile alone does not meet this gate.

## Scope and safety

Only build workspace generation, CI diagnostics, source contracts and engineering docs change. The pinned Engine source is unchanged. CloneStore remains the active production persistence source; Room remains opt-in/debug-only. No user Clone data, account, credential, or session is accessed or modified.
