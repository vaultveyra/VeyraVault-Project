#!/usr/bin/env python3
import os, re, sys, glob, shutil, stat, subprocess, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE = os.path.join(ROOT, "build_workspace")
BUNDLED_ENGINE = os.path.join(ROOT, "engine_source")
OUTPUT_DIR = os.path.join(ROOT, "output_artifacts")

# NDK pinned to a stable release that builds BOTH armeabi-v7a and arm64-v8a for legacy C++ code
NDK_VERSION = "27.0.12077973"
ENGINE_COMMIT = "89b59836c66f173756a4ae258cf379a957649820"
ENGINE_REPOSITORY = "https://github.com/ALEX5402/NewBlackbox.git"
CPU_FEATURES_COMMIT = "4814778e45acc394b37ca0837441ad32a2305bb1"
CPU_FEATURES_REPOSITORY = "https://github.com/google/cpu_features.git"
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
            // Reject a redirected root before using its canonical target as the trust boundary.
            if (FileUtils.isSymlink(root)) return false;
            File canonicalRoot = root.getCanonicalFile();
            File canonicalDirectory = directory.getCanonicalFile();
            if (!canonicalRoot.isDirectory() || !canonicalRoot.canRead()) return false;

            String rootPrefix = canonicalRoot.getPath() + File.separator;
            if (!canonicalDirectory.getPath().startsWith(rootPrefix)) return false;
            if (FileUtils.isSymlink(directory)) return false;

            File ancestor = directory.getParentFile();
            while (ancestor != null) {
                File canonicalAncestor = ancestor.getCanonicalFile();
                if (FileUtils.isSymlink(ancestor)) return false;
                if (canonicalAncestor.equals(canonicalRoot)) return true;
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
        r"        String packageName = ps\.pkg\.packageName;\n[\s\S]*?        return 0;\n    }",
        """        String packageName = ps.pkg.packageName;
        // VEYRAVAULT_VERIFY_CLONE_DATA_RESET
        File internalRoot = BEnvironment.getVirtualRoot();
        File externalRoot = BEnvironment.getExternalVirtualRoot();
        File dataLibraryDirectory = BEnvironment.getDataLibDir(packageName, userId);
        if (!isSafeDirectoryPath(internalRoot, dataLibraryDirectory)) {
            return -1;
        }
        FileUtils.deleteDir(dataLibraryDirectory);
        if (dataLibraryDirectory.exists()) {
            return -1;
        }

        File[] requiredRoots = new File[] {
                internalRoot,
                internalRoot,
                internalRoot,
                internalRoot,
                internalRoot,
                externalRoot
        };
        File[] requiredDirectories = new File[] {
                BEnvironment.getDataDir(packageName, userId),
                BEnvironment.getDataCacheDir(packageName, userId),
                BEnvironment.getDataFilesDir(packageName, userId),
                BEnvironment.getDataDatabasesDir(packageName, userId),
                BEnvironment.getDeDataDir(packageName, userId),
                BEnvironment.getExternalObbDir(packageName, userId)
        };
        // Validate every target before the first mkdir to avoid following an
        // existing symlink or creating part of the reset tree under a bad root.
        for (int i = 0; i < requiredDirectories.length; i++) {
            if (!isSafeDirectoryPath(requiredRoots[i], requiredDirectories[i])) {
                return -1;
            }
        }
        for (int i = 0; i < requiredDirectories.length; i++) {
            File directory = requiredDirectories[i];
            if (!directory.isDirectory() && !directory.mkdirs() && !directory.isDirectory()) {
                return -1;
            }
        }
        return 0;
    }

    /**
     * Validates reset targets beneath their expected virtual roots. Symlinked roots,
     * final directories, and package/user ancestors are rejected; inspection errors fail closed.
     */
    private static boolean isSafeDirectoryPath(File root, File directory) {
        if (root == null || directory == null) return false;
        try {
            if (FileUtils.isSymlink(root)) return false;
            File canonicalRoot = root.getCanonicalFile();
            File canonicalDirectory = directory.getCanonicalFile();
            if (!canonicalRoot.isDirectory() || !canonicalRoot.canRead()) return false;
            String rootPrefix = canonicalRoot.getPath() + File.separator;
            if (!canonicalDirectory.getPath().startsWith(rootPrefix)) return false;
            if (FileUtils.isSymlink(directory)) return false;

            File ancestor = directory.getParentFile();
            while (ancestor != null) {
                File canonicalAncestor = ancestor.getCanonicalFile();
                if (FileUtils.isSymlink(ancestor)) return false;
                if (canonicalAncestor.equals(canonicalRoot)) return true;
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
        ("File dataLibraryDirectory", "isSafeDirectoryPath(internalRoot, dataLibraryDirectory)",
         "File[] requiredRoots", "File[] requiredDirectories",
         "BEnvironment.getExternalObbDir(packageName, userId)",
         "isSafeDirectoryPath(requiredRoots[i], requiredDirectories[i])",
         "FileUtils.isSymlink(root)", "FileUtils.isSymlink(directory)",
         "FileUtils.isSymlink(ancestor)", "directory.mkdirs()", "return -1;"),
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



def align_native_application_platform(workspace, min_sdk):
    """Let Gradle externalNativeBuild derive APP_PLATFORM from minSdkVersion."""
    application_mk = os.path.join(
        workspace, "Bcore", "src", "main", "cpp", "Application.mk"
    )
    if not os.path.isfile(application_mk):
        raise RuntimeError("Pinned Engine Application.mk is missing; native API level is unverified")
    with open(application_mk, "r", encoding="utf-8", errors="ignore") as source_file:
        content = source_file.read()
    pattern = r"^[ \t]*APP_PLATFORM[ \t]*:=.*(?:\r?\n|$)"
    updated, count = re.subn(pattern, "", content, flags=re.M)
    if count > 1:
        raise RuntimeError("Application.mk contains multiple APP_PLATFORM overrides")
    if re.search(r"^[ \t]*APP_PLATFORM[ \t]*:=", updated, flags=re.M):
        raise RuntimeError("APP_PLATFORM override remained after normalization")
    if count:
        with open(application_mk, "w", encoding="utf-8") as output_file:
            output_file.write(updated)
        print("[+] Removed stale Application.mk APP_PLATFORM override; Gradle minSdk {} controls externalNativeBuild.".format(min_sdk))
    else:
        print("[+] Application.mk has no APP_PLATFORM override; Gradle minSdk {} controls externalNativeBuild.".format(min_sdk))


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

    min_sdk = detect_workspace_min_sdk(WORKSPACE)
    run(
        f'python3 "{os.path.join(ROOT, "scripts", "audit_apk.py")}" '
        f'"{apk_out}" --min-api {min_sdk}'
    )

    apk_rep = os.path.join(ROOT, "apk_audit_report.txt")
    if os.path.exists(apk_rep):
        shutil.copy2(apk_rep, os.path.join(OUTPUT_DIR, "apk_audit_report.txt"))
    print("[+] All release artifacts collected in output_artifacts/!")


def detect_workspace_min_sdk(workspace):
    """Require application and Engine root Gradle minSdk values to agree."""
    candidates = {
        "application": os.path.join(workspace, "app", "build.gradle"),
        "Engine root": os.path.join(workspace, "build.gradle"),
    }
    values = {}
    pattern = r"^[ \t]*minSdk(?:Version)?[ \t]*(?:=[ \t]*)?(\d+)"
    for label, path in candidates.items():
        if not os.path.isfile(path):
            raise RuntimeError("{} Gradle file is missing; cannot verify minSdk".format(label))
        with open(path, "r", encoding="utf-8", errors="ignore") as source_file:
            match = re.search(pattern, source_file.read(), flags=re.M)
        if not match:
            raise RuntimeError("{} minSdk is not a numeric literal".format(label))
        values[label] = int(match.group(1))
    if values["application"] != values["Engine root"]:
        raise RuntimeError("Application minSdk {} differs from Engine minSdk {}".format(
            values["application"], values["Engine root"]
        ))
    return values["application"]


def detect_app_java_version(app_gradle_path):
    """Read Java source compatibility from VeyraVault's app module, not the pinned Engine."""
    if not os.path.isfile(app_gradle_path):
        return "VERSION_1_8"
    with open(app_gradle_path, "r", encoding="utf-8", errors="ignore") as app_gradle:
        content = app_gradle.read()
    match = re.search(r'JavaVersion\.(VERSION_[0-9_]+)', content)
    return match.group(1) if match else "VERSION_1_8"


def prepare_armv7_neon_probe(workspace):
    """Add a separate baseline ARMv7 CPU feature probe to the ephemeral Engine workspace."""
    temporary_root = tempfile.mkdtemp(prefix="veyra_cpu_features_")
    try:
        cpu_repository = os.path.join(temporary_root, "cpu_features")
        run(f'git clone --filter=blob:none --no-checkout "{CPU_FEATURES_REPOSITORY}" "{cpu_repository}"')
        run(f'git -C "{cpu_repository}" fetch --depth 1 origin {CPU_FEATURES_COMMIT}')
        run(f'git -C "{cpu_repository}" checkout --detach FETCH_HEAD')

        head = _git_output(cpu_repository, "rev-parse", "HEAD")
        remote = _git_output(cpu_repository, "remote", "get-url", "origin")
        status = _git_output(cpu_repository, "status", "--porcelain", "--untracked-files=all")
        if head != CPU_FEATURES_COMMIT or remote != CPU_FEATURES_REPOSITORY or status:
            raise RuntimeError("Google cpu_features checkout did not match its immutable source pin")

        native_root = os.path.join(workspace, "Bcore", "src", "main", "cpp")
        android_mk = os.path.join(native_root, "Android.mk")
        if not os.path.isdir(native_root) or not os.path.isfile(android_mk):
            raise RuntimeError("Pinned Engine native build directory is missing")

        vendored = os.path.join(native_root, "veyra_cpu_features")
        if os.path.exists(vendored):
            raise RuntimeError("Unexpected pre-existing cpu_features workspace directory")
        shutil.copytree(os.path.join(cpu_repository, "include"), os.path.join(vendored, "include"))
        shutil.copytree(os.path.join(cpu_repository, "src"), os.path.join(vendored, "src"))
        shutil.copy2(os.path.join(cpu_repository, "LICENSE"), os.path.join(vendored, "LICENSE"))
        shutil.copy2(
            os.path.join(ROOT, "app", "src", "main", "cpp", "VeyraNeonProbe.cpp"),
            os.path.join(native_root, "VeyraNeonProbe.cpp"),
        )

        with open(android_mk, "r", encoding="utf-8") as source_file:
            makefile = source_file.read()
        marker = "# VEYRAVAULT_STAGE_8_33_ARMV7_NEON_PROBE"
        if marker in makefile:
            raise RuntimeError("Stage 8.33 NEON probe was already injected into the workspace")
        module = "\n# VEYRAVAULT_STAGE_8_33_ARMV7_NEON_PROBE\n# This helper is separate from libblackbox.so and must never use NEON.\ninclude $(CLEAR_VARS)\nLOCAL_MODULE := veyra_neon_probe\nLOCAL_SRC_FILES := VeyraNeonProbe.cpp\nifeq ($(TARGET_ARCH_ABI),armeabi-v7a)\n# NDK r24+ rejects LOCAL_ARM_NEON := false. Override the default ARMv7\n# target feature for this isolated probe without changing libblackbox.so.\nLOCAL_CFLAGS += -mfpu=vfpv3-d16\nLOCAL_CPPFLAGS += -mfpu=vfpv3-d16\nLOCAL_SRC_FILES += \\\n    veyra_cpu_features/src/filesystem.c \\\n    veyra_cpu_features/src/stack_line_reader.c \\\n    veyra_cpu_features/src/string_view.c \\\n    veyra_cpu_features/src/hwcaps.c \\\n    veyra_cpu_features/src/hwcaps_linux_or_android.c \\\n    veyra_cpu_features/src/impl_arm_linux_or_android.c\nLOCAL_C_INCLUDES += \\\n    $(LOCAL_PATH)/veyra_cpu_features/include \\\n    $(LOCAL_PATH)/veyra_cpu_features/include/internal\nLOCAL_CFLAGS += -std=c99 -DHAVE_DLFCN_H -DSTACK_LINE_READER_BUFFER_SIZE=1024\nLOCAL_LDLIBS += -ldl\nendif\nLOCAL_CPPFLAGS += -std=c++17\ninclude $(BUILD_SHARED_LIBRARY)\n"
        with open(android_mk, "a", encoding="utf-8") as target_file:
            target_file.write(module)

        print("[+] Added isolated ARMv7 NEON preflight probe from google/cpu_features@" + CPU_FEATURES_COMMIT)
        print("[+] The ARMv7 probe uses -mfpu=vfpv3-d16; libblackbox.so is unchanged.")
    finally:
        shutil.rmtree(temporary_root, ignore_errors=True)


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
    # Keep VeyraVault app compatibility independent from the pinned Engine module.
    app_java_ver = detect_app_java_version(os.path.join(ROOT, "app", "build.gradle"))

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

    print(f"[+] Detected Engine Config -> compileSdk: {compile_sdk}, minSdk: {min_sdk}; app Java: {app_java_ver}")
    align_native_application_platform(WORKSPACE, int(min_sdk))
    prepare_armv7_neon_probe(WORKSPACE)

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
            // Do not embed AGP's VCS metadata in the distributable APK.
            vcsInfo {{
                include = false
            }}
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
        sourceCompatibility JavaVersion.{app_java_ver}
        targetCompatibility JavaVersion.{app_java_ver}
    }}

    buildFeatures {{
        buildConfig true
    }}

    lint {{
        checkReleaseBuilds false
        abortOnError false
    }}

    packaging {{
        jniLibs {{
            pickFirsts += ["lib/armeabi-v7a/*.so", "lib/arm64-v8a/*.so"]
        }}
        resources {{
            // Exclude only known non-runtime metadata. Do not remove META-INF/services.
            excludes += [
                "META-INF/DEPENDENCIES",
                "META-INF/LICENSE",
                "META-INF/NOTICE",
                "META-INF/*.version",
                "META-INF/com/android/build/gradle/app-metadata.properties",
                "META-INF/version-control-info.textproto"
            ]
        }}
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
    // Room is an opt-in migration/test foundation: package it only in Debug.
    // Release keeps compile-time types while CloneStore remains the active runtime store.
    debugImplementation 'androidx.room:room-runtime:2.6.1'
    releaseCompileOnly 'androidx.room:room-runtime:2.6.1'
    debugAnnotationProcessor 'androidx.room:room-compiler:2.6.1'
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
