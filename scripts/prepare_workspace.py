#!/usr/bin/env python3
import os, re, sys, glob, shutil, stat, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE = os.path.join(ROOT, "build_workspace")
BUNDLED_ENGINE = os.path.join(ROOT, "engine_source")
OUTPUT_DIR = os.path.join(ROOT, "output_artifacts")

# NDK pinned to a stable release that builds BOTH armeabi-v7a and arm64-v8a for legacy C++ code
NDK_VERSION = "27.0.12077973"
ENGINE_COMMIT = "89b59836c66f173756a4ae258cf379a957649820"
ENGINE_REPOSITORY = "https://github.com/ALEX5402/NewBlackbox.git"
NDK_LICENSE_HASH = "24333f8a63b6825ea9c5514f83c2829b004d1fee"


def run(cmd, cwd=None, check=True):
    print(f"[+] Executing: {cmd}")
    subprocess.run(cmd, shell=True, cwd=cwd, check=check)



def _git_output(repository_path, *arguments):
    try:
        result = subprocess.run(
            ["git", "-C", repository_path, *arguments],
            text=True,
            capture_output=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise RuntimeError("Could not verify the bundled/pinned Engine Git checkout") from error
    return result.stdout.strip()


def verify_engine_source(repository_path):
    """Fail closed unless the Engine source is the exact clean pinned upstream checkout."""
    if os.path.islink(repository_path) or not os.path.isdir(repository_path):
        raise RuntimeError("Engine source path is missing or is a symbolic link")
    git_dir = os.path.join(repository_path, ".git")
    if os.path.islink(git_dir) or not os.path.isdir(git_dir):
        raise RuntimeError("Engine source must be a full Git checkout; unverified source bundles are refused")
    if not os.path.isdir(os.path.join(repository_path, "Bcore")):
        raise RuntimeError("Engine source is missing the expected Bcore module")

    head = _git_output(repository_path, "rev-parse", "HEAD")
    if head != ENGINE_COMMIT:
        raise RuntimeError("Engine source HEAD does not match the required immutable pin")

    remote = _git_output(repository_path, "remote", "get-url", "origin")
    if remote != ENGINE_REPOSITORY:
        raise RuntimeError("Engine source origin does not match the approved upstream repository")

    status = _git_output(repository_path, "status", "--porcelain", "--untracked-files=all")
    if status:
        raise RuntimeError("Engine source working tree is not clean; refusing an unverified build")

    ignored = _git_output(repository_path, "ls-files", "--others", "--ignored", "--exclude-standard")
    if ignored:
        raise RuntimeError("Engine source contains ignored untracked files; refusing an unverified build")

    print(f"[+] Verified Engine source: {ENGINE_REPOSITORY}@{ENGINE_COMMIT}")




def _read_engine_source_file(workspace, relative_path):
    path = os.path.join(workspace, *relative_path.split("/"))
    if not os.path.isfile(path):
        raise RuntimeError("Pinned Engine cleanup source is missing: " + relative_path)
    with open(path, "r", encoding="utf-8") as source_file:
        return path, source_file.read()


def _patch_engine_fragment(source, marker, pattern, replacement, required, label):
    if marker in source:
        if any(item not in source for item in required):
            raise RuntimeError("Partially applied or unexpected Engine hardening in " + label)
        return source
    updated, count = re.subn(pattern, replacement, source, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError("Pinned Engine cleanup source no longer matches the audited layout: " + label)
    if any(item not in updated for item in required):
        raise RuntimeError("Engine cleanup patch verification failed in " + label)
    return updated


def _add_engine_file_import(source, label):
    if "import java.io.File;" in source:
        return source
    import_line = "import top.niunaijun.blackbox.utils.FileUtils;"
    if source.count(import_line) != 1:
        raise RuntimeError("Pinned Engine import layout changed: " + label)
    return source.replace(import_line, "import java.io.File;\n" + import_line, 1)


def harden_clone_cleanup_semantics(workspace):
    """Fail closed on incomplete Clone cleanup in the verified, ephemeral Engine build workspace."""
    relative = {
        "remove_user": "Bcore/src/main/java/top/niunaijun/blackbox/core/system/pm/installer/RemoveUserExecutor.java",
        "remove_app": "Bcore/src/main/java/top/niunaijun/blackbox/core/system/pm/installer/RemoveAppExecutor.java",
        "create_user": "Bcore/src/main/java/top/niunaijun/blackbox/core/system/pm/installer/CreateUserExecutor.java",
        "installer": "Bcore/src/main/java/top/niunaijun/blackbox/core/system/pm/BPackageInstallerService.java",
        "manager": "Bcore/src/main/java/top/niunaijun/blackbox/core/system/pm/BPackageManagerService.java",
    }
    paths = {}
    source = {}
    for key, value in relative.items():
        paths[key], source[key] = _read_engine_source_file(workspace, value)

    remove_user = _add_engine_file_import(source["remove_user"], relative["remove_user"])
    remove_user = _patch_engine_fragment(
        remove_user,
        "VEYRAVAULT_CHECK_CLONE_USER_DATA_REMOVAL",
        r"        String packageName = ps\.pkg\.packageName;\n[\s\S]*?        return 0;\n    }",
        """        String packageName = ps.pkg.packageName;
        // VEYRAVAULT_CHECK_CLONE_USER_DATA_REMOVAL
        File[] dataRoots = new File[] {
                BEnvironment.getVirtualRoot(),
                BEnvironment.getVirtualRoot(),
                BEnvironment.getExternalVirtualRoot(),
                BEnvironment.getExternalVirtualRoot()
        };
        File[] dataDirectories = new File[] {
                BEnvironment.getDataDir(packageName, userId),
                BEnvironment.getDeDataDir(packageName, userId),
                BEnvironment.getExternalDataDir(packageName, userId),
                BEnvironment.getExternalObbDir(packageName, userId)
        };
        for (int i = 0; i < dataDirectories.length; i++) {
            File directory = dataDirectories[i];
            if (!isSafeDirectoryPath(dataRoots[i], directory)) {
                return -1;
            }
            FileUtils.deleteDir(directory);
            if (directory.exists()) {
                return -1;
            }
        }
        return 0;
    }

    /**
     * Refuses to recurse through paths outside the virtual root or through symlinked
     * package/user ancestors. Filesystem inspection errors fail closed.
     */
    private static boolean isSafeDirectoryPath(File root, File directory) {
        if (root == null || directory == null) return false;
        try {
            File canonicalRoot = root.getCanonicalFile();
            File canonicalDirectory = directory.getCanonicalFile();
            if (!canonicalRoot.isDirectory() || !canonicalRoot.canRead()) return false;

            String rootPrefix = canonicalRoot.getPath() + File.separator;
            if (!canonicalDirectory.getPath().startsWith(rootPrefix)) return false;
            if (FileUtils.isSymlink(directory)) return false;

            File ancestor = directory.getParentFile();
            while (ancestor != null) {
                File canonicalAncestor = ancestor.getCanonicalFile();
                if (canonicalAncestor.equals(canonicalRoot)) return true;
                if (FileUtils.isSymlink(ancestor)) return false;
                if (canonicalAncestor.exists()
                        && (!canonicalAncestor.isDirectory() || !canonicalAncestor.canRead())) {
                    return false;
                }
                ancestor = ancestor.getParentFile();
            }
        } catch (Exception ignored) {
            return false;
        }
        return false;
    }""",
        ("File[] dataRoots", "File[] dataDirectories",
         "BEnvironment.getExternalObbDir(packageName, userId)",
         "isSafeDirectoryPath(dataRoots[i], directory)",
         "private static boolean isSafeDirectoryPath(",
         "FileUtils.isSymlink(directory)", "FileUtils.isSymlink(ancestor)",
         "canonicalDirectory.getPath().startsWith(rootPrefix)", "return -1;"),
        relative["remove_user"],
    )

    remove_app = _add_engine_file_import(source["remove_app"], relative["remove_app"])
    remove_app = _patch_engine_fragment(
        remove_app,
        "VEYRAVAULT_CHECK_CLONE_APP_REMOVAL",
        r"        FileUtils\.deleteDir\(BEnvironment\.getAppDir\(ps\.pkg\.packageName\)\);\n        return 0;",
        """        // VEYRAVAULT_CHECK_CLONE_APP_REMOVAL
        File appDirectory = BEnvironment.getAppDir(ps.pkg.packageName);
        FileUtils.deleteDir(appDirectory);
        if (appDirectory.exists()) {
            return -1;
        }
        return 0;""",
        ("File appDirectory", "FileUtils.deleteDir(appDirectory)",
         "if (appDirectory.exists())", "return -1;"),
        relative["remove_app"],
    )

    create_user = _add_engine_file_import(source["create_user"], relative["create_user"])
    create_user = _patch_engine_fragment(
        create_user,
        "VEYRAVAULT_VERIFY_CLONE_DATA_RESET",
        r"        String packageName = ps\.pkg\.packageName;\n[\s\S]*?        return 0;",
        """        String packageName = ps.pkg.packageName;
        // VEYRAVAULT_VERIFY_CLONE_DATA_RESET
        File dataLibraryDirectory = BEnvironment.getDataLibDir(packageName, userId);
        FileUtils.deleteDir(dataLibraryDirectory);
        if (dataLibraryDirectory.exists()) {
            return -1;
        }

        File[] requiredDirectories = new File[] {
                BEnvironment.getDataDir(packageName, userId),
                BEnvironment.getDataCacheDir(packageName, userId),
                BEnvironment.getDataFilesDir(packageName, userId),
                BEnvironment.getDataDatabasesDir(packageName, userId),
                BEnvironment.getDeDataDir(packageName, userId),
                BEnvironment.getExternalObbDir(packageName, userId)
        };
        for (File directory : requiredDirectories) {
            if (!directory.isDirectory() && !directory.mkdirs() && !directory.isDirectory()) {
                return -1;
            }
        }
        return 0;""",
        ("File dataLibraryDirectory", "dataLibraryDirectory.exists()",
         "File[] requiredDirectories", "directory.mkdirs()", "directory.isDirectory()",
         "BEnvironment.getDataCacheDir(packageName, userId)",
         "BEnvironment.getDataFilesDir(packageName, userId)",
         "BEnvironment.getDataDatabasesDir(packageName, userId)",
         "BEnvironment.getExternalObbDir(packageName, userId)"),
        relative["create_user"],
    )

    installer = _patch_engine_fragment(
        source["installer"],
        "VEYRAVAULT_REMOVE_USER_DATA_BEFORE_APP_BINARY",
        r"        if \(removeApp\) \{\n\s*executors\.add\(new RemoveAppExecutor\(\)\);\n\s*\}\n\s*executors\.add\(new RemoveUserExecutor\(\)\);",
        """        // VEYRAVAULT_REMOVE_USER_DATA_BEFORE_APP_BINARY
        executors.add(new RemoveUserExecutor());
        if (removeApp) {
            executors.add(new RemoveAppExecutor());
        }""",
        ("executors.add(new RemoveUserExecutor());",
         "executors.add(new RemoveAppExecutor());"),
        relative["installer"],
    )

    manager = _patch_engine_fragment(
        source["manager"],
        "VEYRAVAULT_KEEP_CLONE_INSTALLED_ON_UNINSTALL_CLEANUP_FAILURE",
        r"                int i = BPackageInstallerService\.get\(\)\.uninstallPackageAsUser\(ps, removeApp, userId\);\n                if \(i < 0\) \{\s*\}",
        """                // VEYRAVAULT_KEEP_CLONE_INSTALLED_ON_UNINSTALL_CLEANUP_FAILURE
                int cleanupResult = BPackageInstallerService.get().uninstallPackageAsUser(ps, removeApp, userId);
                if (cleanupResult != 0) {
                    return;
                }""",
        ("cleanupResult != 0", "return;"),
        relative["manager"],
    )
    manager = _patch_engine_fragment(
        manager,
        "VEYRAVAULT_KEEP_ALL_CLONE_METADATA_ON_BULK_CLEANUP_FAILURE",
        r"                        int i = BPackageInstallerService\.get\(\)\.uninstallPackageAsUser\(ps, true, userId\);\n                        if \(i < 0\) \{\n                            continue;\n                        \}",
        """                        // VEYRAVAULT_KEEP_ALL_CLONE_METADATA_ON_BULK_CLEANUP_FAILURE
                        int cleanupResult = BPackageInstallerService.get().uninstallPackageAsUser(ps, true, userId);
                        if (cleanupResult != 0) {
                            return;
                        }""",
        ("cleanupResult != 0", "return;"),
        relative["manager"],
    )
    manager = _patch_engine_fragment(
        manager,
        "VEYRAVAULT_PROPAGATE_CLONE_CLEAR_DATA_FAILURE",
        r"        int i = BPackageInstallerService\.get\(\)\.clearPackage\(ps, userId\);",
        """        // VEYRAVAULT_PROPAGATE_CLONE_CLEAR_DATA_FAILURE
        int cleanupResult = BPackageInstallerService.get().clearPackage(ps, userId);
        if (cleanupResult != 0) {
            throw new IllegalStateException(
                    "VeyraVault Clone data reset failed; partial cleanup may have occurred. result="
                            + cleanupResult);
        }""",
        ("cleanupResult != 0", "throw new IllegalStateException("),
        relative["manager"],
    )

    # All source fragments are verified before any file is written.
    transformed = {
        "remove_user": remove_user,
        "remove_app": remove_app,
        "create_user": create_user,
        "installer": installer,
        "manager": manager,
    }
    for key, content in transformed.items():
        with open(paths[key], "w", encoding="utf-8") as output_file:
            output_file.write(content)

    print("[+] Pinned Engine Clone cleanup fails closed on residual directories and failed reset-directory recreation.")


def accept_android_sdk_licenses():
    print("[*] Accepting Android SDK & NDK licenses...")
    sdk_dirs = []
    for p in [os.environ.get("ANDROID_HOME"), os.environ.get("ANDROID_SDK_ROOT"),
              "/usr/local/lib/android/sdk"]:
        if p and os.path.isdir(p) and p not in sdk_dirs:
            sdk_dirs.append(p)

    for sdk in sdk_dirs:
        lic_dir = os.path.join(sdk, "licenses")
        os.makedirs(lic_dir, exist_ok=True)

        sdk_hashes = [
            "8933bad161af4178b1185d1a37fbf41ea5269c55",
            "d56f5187479451eabf01fb78af6dfcb131a6481e",
            NDK_LICENSE_HASH,
            "859f317696f67ef3d7f30a50a5560e7834b43903",
        ]
        with open(os.path.join(lic_dir, "android-sdk-license"), "w", encoding="utf-8") as f:
            f.write("\n" + "\n".join(sdk_hashes) + "\n")

        with open(os.path.join(lic_dir, "android-ndk-license"), "w", encoding="utf-8") as f:
            f.write("\n" + NDK_LICENSE_HASH + "\n")

        preview_hashes = [
            "84831b9409646a918e30573bab4c9c91346d8abd",
            "504667f4c0de7af1a06de9f4b1727b84351f2910",
        ]
        with open(os.path.join(lic_dir, "android-sdk-preview-license"), "w", encoding="utf-8") as f:
            f.write("\n" + "\n".join(preview_hashes) + "\n")

        sdkmgr = os.path.join(sdk, "cmdline-tools", "latest", "bin", "sdkmanager")
        if os.path.exists(sdkmgr):
            run(f"yes | {sdkmgr} --licenses", check=False)


def pin_ndk_version(gradle_file, label):
    if not os.path.exists(gradle_file):
        print(f"[-] {label}: build.gradle not found, NDK pin skipped.")
        return
    with open(gradle_file, "r", encoding="utf-8", errors="ignore") as f:
        txt = f.read()
    ndk_line = f'    ndkVersion "{NDK_VERSION}"'
    if re.search(r'^[ \t]*ndkVersion\b.*$', txt, flags=re.M):
        txt = re.sub(r'^[ \t]*ndkVersion\b.*$', ndk_line, txt, flags=re.M)
        status = "replaced"
    else:
        txt, n = re.subn(r'^([ \t]*android[ \t]*\{[ \t\r]*)$',
                         lambda m: m.group(1) + "\n" + ndk_line,
                         txt, count=1, flags=re.M)
        if n == 0:
            txt, n = re.subn(r'(\bandroid\s*\{)',
                             lambda m: m.group(1) + "\n" + ndk_line,
                             txt, count=1)
        status = "inserted" if n else "NOT FOUND"
    with open(gradle_file, "w", encoding="utf-8") as f:
        f.write(txt)
    print(f"[+] {label}: ndkVersion {NDK_VERSION} -> {status}")



def disable_remote_log_upload(workspace):
    """Disable upstream BlackBox log transmission before compiling the engine."""
    config_path = os.path.join(workspace, "Bcore", "src", "main", "java", "top", "niunaijun", "blackbox", "app", "configuration", "ClientConfiguration.java")
    sender_path = os.path.join(workspace, "Bcore", "src", "main", "java", "top", "niunaijun", "blackbox", "utils", "LogSender.java")
    if not os.path.isfile(config_path) or not os.path.isfile(sender_path):
        raise RuntimeError("Pinned engine layout changed; refusing an unverified build")

    with open(config_path, "r", encoding="utf-8") as f:
        config = f.read()
    if "VEYRAVAULT_REMOTE_LOG_UPLOAD_DISABLED" not in config:
        pattern = r'public\s+String\s+getLogSenderChatId\s*\(\s*\)\s*\{[^}]*\}'
        replacement = "/* VEYRAVAULT_REMOTE_LOG_UPLOAD_DISABLED */\n    public String getLogSenderChatId() {\n        return null;\n    }"
        config, count = re.subn(pattern, replacement, config, count=1, flags=re.S)
        if count != 1:
            raise RuntimeError("Could not safely disable upstream log-upload destination")
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(config)

    with open(sender_path, "r", encoding="utf-8") as f:
        sender = f.read()
    if "VEYRAVAULT_REMOTE_LOG_UPLOAD_DISABLED" not in sender:
        if "logs-sender-api.vercel.app" not in sender:
            raise RuntimeError("Unexpected LogSender source; refusing an unverified engine build")
        stub = (
            "package top.niunaijun.blackbox.utils;\n\n"
            "import java.io.File;\n\n"
            "/** VEYRAVAULT_REMOTE_LOG_UPLOAD_DISABLED: remote log transmission is disabled. */\n"
            "public final class LogSender {\n"
            "    private LogSender() { }\n"
            "    public static String send(String chatId, File logFile, String caption) {\n"
            "        return \"Remote log upload disabled by VeyraVault security policy\";\n"
            "    }\n"
            "}\n"
        )
        with open(sender_path, "w", encoding="utf-8") as f:
            f.write(stub)
    print("[+] Upstream BlackBox remote crash/log upload disabled and verified.")


def post_build():
    print("[*] Collecting APK and running Stage-2 binary audit...")
    if os.path.isdir(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    apks = glob.glob(os.path.join(WORKSPACE, "app", "build", "outputs", "apk", "release", "*.apk"))
    if not apks:
        print("[-] ERROR: No release APK found!")
        sys.exit(1)
    apk_out = os.path.join(OUTPUT_DIR, "VeyraVault-release.apk")
    shutil.copy2(apks[0], apk_out)

    src_rep = os.path.join(ROOT, "source_audit_report.txt")
    if os.path.exists(src_rep):
        shutil.copy2(src_rep, os.path.join(OUTPUT_DIR, "source_audit_report.txt"))

    run(f'python3 "{os.path.join(ROOT, "scripts", "audit_apk.py")}" "{apk_out}"')

    apk_rep = os.path.join(ROOT, "apk_audit_report.txt")
    if os.path.exists(apk_rep):
        shutil.copy2(apk_rep, os.path.join(OUTPUT_DIR, "apk_audit_report.txt"))
    print("[+] All release artifacts collected in output_artifacts/!")


def main():
    if "--post-build" in sys.argv:
        post_build()
        return

    accept_android_sdk_licenses()

    if os.path.exists(WORKSPACE):
        shutil.rmtree(WORKSPACE)

    if os.path.exists(os.path.join(BUNDLED_ENGINE, "Bcore")):
        print("[+] Verifying bundled Engine before copying...")
        verify_engine_source(BUNDLED_ENGINE)
        print("[+] Copying bundled Bcore engine to build_workspace...")
        shutil.copytree(BUNDLED_ENGINE, WORKSPACE)
    else:
        print("[*] Cloning upstream BlackBox engine into build_workspace...")
        run(f'git clone --no-checkout "{ENGINE_REPOSITORY}" "{WORKSPACE}"')
        run(f'git -C "{WORKSPACE}" fetch --depth 1 origin {ENGINE_COMMIT}')
        run(f'git -C "{WORKSPACE}" checkout --detach FETCH_HEAD')

    verify_engine_source(WORKSPACE)
    harden_clone_cleanup_semantics(WORKSPACE)
    disable_remote_log_upload(WORKSPACE)

    gradlew_path = os.path.join(WORKSPACE, "gradlew")
    if os.path.exists(gradlew_path):
        st = os.stat(gradlew_path)
        os.chmod(gradlew_path, st.st_mode | stat.S_IEXEC)

    bcore_gradle = os.path.join(WORKSPACE, "Bcore", "build.gradle")
    orig_app_gradle = os.path.join(WORKSPACE, "app", "build.gradle")
    root_gradle = os.path.join(WORKSPACE, "build.gradle")
    toml_path = os.path.join(WORKSPACE, "gradle", "libs.versions.toml")

    compile_sdk = "34"
    min_sdk = "21"
    java_ver = "VERSION_1_8"

    for gpath in [orig_app_gradle, bcore_gradle, root_gradle, toml_path]:
        if os.path.exists(gpath):
            with open(gpath, "r", encoding="utf-8", errors="ignore") as f:
                txt = f.read()
            m = re.search(r'compileSdk(?:Version)?\s*[=:]?\s*["\']?(\d+)["\']?', txt)
            if m:
                compile_sdk = m.group(1)
            m = re.search(r'minSdk(?:Version)?\s*[=:]?\s*["\']?(\d+)["\']?', txt)
            if m:
                min_sdk = m.group(1)
            m = re.search(r'JavaVersion\.(VERSION_[0-9_]+)', txt)
            if m:
                java_ver = m.group(1)

    print(f"[+] Detected Engine Config -> compileSdk: {compile_sdk}, minSdk: {min_sdk}, Java: {java_ver}")

    bcore_manifest = os.path.join(WORKSPACE, "Bcore", "src", "main", "AndroidManifest.xml")
    if os.path.exists(bcore_manifest):
        with open(bcore_manifest, "r", encoding="utf-8", errors="ignore") as f:
            bm = f.read()
        for attr in ["android:label", "android:icon", "android:roundIcon",
                     "android:allowBackup", "android:supportsRtl", "android:theme"]:
            bm = re.sub(rf'\s+{attr}="[^"]*"', '', bm)
        with open(bcore_manifest, "w", encoding="utf-8") as f:
            f.write(bm)

    # Pin a stable NDK for the native engine (fixes the armeabi-v7a native build failure on NDK 29)
    pin_ndk_version(bcore_gradle, "Bcore")

    ws_app = os.path.join(WORKSPACE, "app")
    if os.path.exists(ws_app):
        shutil.rmtree(ws_app)
    shutil.copytree(os.path.join(ROOT, "app"), ws_app)

    manifest_path = os.path.join(ws_app, "src", "main", "AndroidManifest.xml")
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            m_txt = f.read()
        m_txt = re.sub(r'\s+package="com\.veyravault\.space"', '', m_txt)
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(m_txt)

    app_gradle_content = f"""plugins {{
    id 'com.android.application'
}}

android {{
    namespace "com.veyravault.space"
    compileSdk {compile_sdk}
    ndkVersion "{NDK_VERSION}"

    defaultConfig {{
        applicationId "com.veyravault.space"
        minSdk {min_sdk}
        javaCompileOptions {{
            annotationProcessorOptions {{
                arguments += ["room.schemaLocation": "$projectDir/schemas".toString()]
            }}
        }}
        targetSdk 28
        testInstrumentationRunner "androidx.test.runner.AndroidJUnitRunner"
        versionCode 200
        versionName "2.0.0-Enterprise"

        ndk {{
            abiFilters "armeabi-v7a", "arm64-v8a"
        }}
    }}

    buildTypes {{
        release {{
            minifyEnabled false
            shrinkResources false
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }}
        // Debug instrumentation exercises Room without starting the virtual engine.
        debug {{
            // The CI emulator is x86_64. Release keeps the production ARM ABI filters above.
            ndk {{
                abiFilters "x86_64"
            }}
            packaging {{
                jniLibs {{
                    excludes += ["**/*.so"]
                }}
            }}
        }}
    }}

    compileOptions {{
        sourceCompatibility JavaVersion.{java_ver}
        targetCompatibility JavaVersion.{java_ver}
    }}

    buildFeatures {{
        buildConfig true
    }}

    lint {{
        checkReleaseBuilds false
        abortOnError false
    }}

    packagingOptions {{
        pickFirst 'lib/armeabi-v7a/*.so'
        pickFirst 'lib/arm64-v8a/*.so'
        exclude 'META-INF/DEPENDENCIES'
        exclude 'META-INF/LICENSE'
        exclude 'META-INF/NOTICE'
    }}
}}

dependencies {{
    // The Room-only debug harness needs Bcore types at compile time, but must not package
    // the ARM-only virtual engine or its native libraries into the x86_64 emulator APK.
    releaseImplementation project(':Bcore')
    debugCompileOnly project(':Bcore')
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation 'com.google.android.material:material:1.9.0'
    implementation 'androidx.recyclerview:recyclerview:1.3.1'
    implementation 'androidx.cardview:cardview:1.0.0'
    implementation 'org.osmdroid:osmdroid-android:6.1.14'
    implementation 'androidx.room:room-runtime:2.6.1'
    annotationProcessor 'androidx.room:room-compiler:2.6.1'
    androidTestImplementation 'androidx.test:runner:1.5.2'
    androidTestImplementation 'androidx.test:core:1.5.0'
    androidTestImplementation 'androidx.test.ext:junit:1.1.5'
}}
"""
    with open(os.path.join(ws_app, "build.gradle"), "w", encoding="utf-8") as f:
        f.write(app_gradle_content)

    settings_gradle = os.path.join(WORKSPACE, "settings.gradle")
    modules = ["':app'", "':Bcore'"]
    if os.path.exists(settings_gradle):
        with open(settings_gradle, "r", encoding="utf-8", errors="ignore") as f:
            stxt = f.read()
        for m in re.findall(r"['\"](:[a-zA-Z0-9_\-:]+)['\"]", stxt):
            q = f"'{m}'"
            if q not in modules:
                modules.append(q)

    inc_block = "\n".join([f"include {m}" for m in modules])
    new_settings = f"""pluginManagement {{
    repositories {{
        google()
        mavenCentral()
        gradlePluginPortal()
        maven {{ url 'https://jitpack.io' }}
    }}
}}
dependencyResolutionManagement {{
    repositoriesMode.set(RepositoriesMode.PREFER_SETTINGS)
    repositories {{
        google()
        mavenCentral()
        maven {{ url 'https://jitpack.io' }}
    }}
}}
rootProject.name = "VeyraVault"
{inc_block}
"""
    with open(settings_gradle, "w", encoding="utf-8") as f:
        f.write(new_settings)

    gradle_props = os.path.join(WORKSPACE, "gradle.properties")
    props_content = """org.gradle.jvmargs=-Xmx4096m -Dfile.encoding=UTF-8 --add-opens=jdk.compiler/com.sun.tools.javac.api=ALL-UNNAMED --add-opens=jdk.compiler/com.sun.tools.javac.code=ALL-UNNAMED --add-opens=jdk.compiler/com.sun.tools.javac.comp=ALL-UNNAMED --add-opens=jdk.compiler/com.sun.tools.javac.file=ALL-UNNAMED --add-opens=jdk.compiler/com.sun.tools.javac.jvm=ALL-UNNAMED --add-opens=jdk.compiler/com.sun.tools.javac.main=ALL-UNNAMED --add-opens=jdk.compiler/com.sun.tools.javac.model=ALL-UNNAMED --add-opens=jdk.compiler/com.sun.tools.javac.parser=ALL-UNNAMED --add-opens=jdk.compiler/com.sun.tools.javac.processing=ALL-UNNAMED --add-opens=jdk.compiler/com.sun.tools.javac.tree=ALL-UNNAMED --add-opens=jdk.compiler/com.sun.tools.javac.util=ALL-UNNAMED
android.useAndroidX=true
android.enableJetifier=true
android.nonTransitiveRClass=false
"""
    with open(gradle_props, "w", encoding="utf-8") as f:
        f.write(props_content)

    print("[+] Workspace and NDK pin prepared. Signing is handled in a separate job; this build step never receives signing secrets.")


if __name__ == "__main__":
    main()
