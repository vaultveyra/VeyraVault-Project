# Stage 8.27 — Minimum Android API and legacy signing verification

## Scope

The app declares minSdkVersion 21 (Android 5.0). Stage 8.27 makes minimum-API validation explicit without changing the pinned Engine source or raising the minimum Android version.

## App and Engine Java levels

- The tracked VeyraVault app module declares Java 8 source/target compatibility.
- The pinned BlackBox Bcore module declares Java 21.
- The old workspace generator scanned the Engine Gradle file after the app Gradle file and reused the last detected Java version for the generated app module. That unintentionally promoted VeyraVault app compilation to Java 21.
- The workspace generator now reads the app level only from the tracked app/build.gradle; Bcore's own Java 21 configuration remains unchanged.
- The Release build still uses compile SDK 35, min SDK 21 and target SDK 28. This separation does not imply that every newer Java library API is available on API 21.

## API-21 runtime coverage

- CI retains the API-34 Android instrumentation run.
- A separate API-21 x86_64 emulator run executes LegacyApi21CompatibilityInstrumentationTest.
- The API-21 test exercises the legacy PackageManager overload, ApplicationInfo splitSourceDirs, APK ZIP preflight, package fingerprint revalidation and the pre-API-23 host-bitness path.
- It also exercises the Calendar-based date formatter and checks that both Kotlin Coroutines ServiceLoader resources remain readable and their provider classes load.
- NativeAbiPreflight keeps Process.is64Bit behind the API-23 guard and PackageManager.ApplicationInfoFlags behind the API-33 guard.

## APK signatures and META-INF resources

- Release signing explicitly enables APK Signature Scheme V1, V2 and V3.
- The isolated signing job verifies all three schemes with min SDK 21; V1 remains required for Android 5/6, which do not verify V2/V3.
- The signed APK contains META-INF/services/kotlinx.coroutines.internal.MainDispatcherFactory and META-INF/services/kotlinx.coroutines.CoroutineExceptionHandler. These are runtime provider descriptors, not disposable version metadata, and are not excluded from packaging.
- The signed JAR manifest and .SF file contain SHA-256 digests for these service descriptor paths. jarsigner -verify reports the archive verified and notes that these entries are signed through JarFile but not through JarInputStream; apksigner also reports META-INF verification warnings. The API-21 smoke test checks runtime resource discovery, but it is not a tamper-resistance test.
- The small AndroidX *.version, Gradle app-metadata and version-control metadata files remain in the package for now. No broad META-INF/** exclusion is introduced because it could remove runtime service providers.

## Validation limits

- API-21 x86_64 emulator coverage is a minimum-OS smoke test; it does not certify ARMv7 hardware, Huawei firmware, vendor-specific storage, or Engine native virtualization on a physical device.
- The API-34 emulator suite and ARM native release packaging remain separate validation tracks.
- No Clone, account, session, credential, or user app data is touched by these tests.
- main remains unchanged; PR #4 remains Open and Draft.
