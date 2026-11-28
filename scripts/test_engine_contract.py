#!/usr/bin/env python3
"""Static regression checks for Engine install/launch failure semantics."""
from pathlib import Path

source = Path("app/src/main/java/com/veyravault/space/core/Engine.java").read_text(encoding="utf-8")

def method_body(signature):
    start = source.index(signature)
    brace = source.index("{", start)
    depth = 0
    for i in range(brace, len(source)):
        if source[i] == "{":
            depth += 1
        elif source[i] == "}":
            depth -= 1
            if depth == 0:
                return source[brace + 1:i]
    raise AssertionError("Unclosed method: " + signature)

install = method_body("public static boolean installPackageAsUser(")
assert "if (core == null) {" in install
assert "if (res == null) {" in install
assert "success.getBoolean(res)" in install
assert "preflight.isAllowed()" in install
assert "preflight.matchesInstalledPackage(context, pkg)" in install
assert install.index("preflight.isAllowed()") < install.index('getMethod("installPackageAsUser", String.class, int.class)')
assert install.index("preflight.matchesInstalledPackage(context, pkg)") < install.index(
    'getMethod("installPackageAsUser", String.class, int.class)'
)
assert "catch (Throwable error)" in install and "return false;" in install

query_installed = method_body("private static Boolean queryInstalledAsUser(")
assert 'getMethod("isInstalled", String.class, int.class)' in query_installed
assert "result instanceof Boolean ? (Boolean) result : null" in query_installed
assert "return null;" in query_installed

launch = method_body("public static CloneLaunchResult launchCloneDetailed(")
assert "CloneInstallState installState = getCloneInstallState(entry.packageName, entry.userId);" in launch
assert "installState == null || installState == CloneInstallState.UNKNOWN" in launch
assert 'new CloneLaunchResult(false, "ENGINE_INSTALL_STATE_UNKNOWN", null)' in launch
assert "installState == CloneInstallState.ABSENT" in launch
assert "NativeAbiPreflight.inspectInstalledPackage(ctx, entry.packageName)" in launch
assert "if (!preflight.isAllowed())" in launch
assert '"NATIVE_ABI_PREFLIGHT_BLOCKED:" + preflight.getDiagnosticCode()' in launch
assert "installPackageAsUser(ctx, entry.packageName, entry.userId, preflight)" in launch
assert "isInstalledAsUser(" not in launch
assert "ENGINE_INSTALL_FAILED" in launch
assert "if (!Boolean.TRUE.equals(value))" in launch
assert launch.index("NativeAbiPreflight.inspectInstalledPackage(ctx, entry.packageName)") < launch.index("installPackageAsUser(ctx, entry.packageName, entry.userId, preflight)")
assert launch.index("installPackageAsUser(ctx, entry.packageName, entry.userId, preflight)") < launch.index("VirtualHookManager.syncCloneHooks(ctx, entry)")
assert launch.index("VirtualHookManager.syncCloneHooks(ctx, entry)") < launch.index('getMethod("launchApk", String.class, int.class)')
assert launch.index("if (!Boolean.TRUE.equals(value))") < launch.index("CloneStore.recordActiveLaunch(ctx, entry)")
assert "r == null || Boolean.TRUE.equals(r)" not in launch
compat = method_body("public static boolean launchClone(")
assert "return launchCloneDetailed(ctx, entry).launched;" in compat
print("Engine install/launch failure contract: PASS")
print("Active-launch marker is written only after confirmed engine launch: PASS")

# Clone creation entry points use the shared transaction coordinator.
main_ui = Path("app/src/main/java/com/veyravault/space/ui/MainActivity.java").read_text(encoding="utf-8")
add_ui = Path("app/src/main/java/com/veyravault/space/ui/AddAppActivity.java").read_text(encoding="utf-8")
provision = Path("app/src/main/java/com/veyravault/space/core/AsyncCloneProvisionRepository.java").read_text(encoding="utf-8")
queue = Path("app/src/main/java/com/veyravault/space/core/EngineOperationQueue.java").read_text(encoding="utf-8")

assert "duplicateCloneWithPreflight(item);" in main_ui
duplicate = main_ui[main_ui.index("private void duplicateCloneWithPreflight("):
                    main_ui.index("private void showRenameDialog(")]
assert "provisionRepository.createClone(item.packageName, item.displayName, fa" in duplicate
assert "Engine.installPackageAsUser(" not in duplicate

add_clone = add_ui[add_ui.index("private void cloneSingleApp("):
                   add_ui.index("private void showCloneError(")]
assert "provisionRepository.createClone(app.pkg, app.label, fa" in add_clone
assert "Engine.installPackageAsUser(" not in add_clone
assert "Engine.uninstallClone(" not in add_clone

assert provision.index("persistence.inspectNativeAbi(packageName") < provision.index("persistence.reserveNextUserId(packageName")
assert provision.index("persistence.reserveNextUserId(packageName") < provision.index("Engine.installPackageAsUser(")
assert provision.index("Engine.installPackageAsUser(") < provision.index("persistence.commitReservedClone(entry, reservation")
assert "Engine.CloneInstallState.ABSENT" in provision
assert "reservation remains blocked" in provision
assert "private static final ExecutorService ENGINE" in queue
assert "veyravault-engine-operations" in queue
assert "repository.allocateNextUserId" not in main_ui + add_ui
assert "launchRepository.launchClone(item.packageName, item.userId" in main_ui
assert "Engine.launchClone(MainActivity.this, item)" not in main_ui
print("Clone creation transaction ordering and shared Engine queue: PASS")

uninstall = method_body("public static boolean uninstallClone(")
assert "queryInstalledAsUser(pkg, userId)" in uninstall
assert "Boolean.FALSE.equals(queryInstalledAsUser(pkg, userId))" in uninstall
assert "return false;" in uninstall
query = method_body("private static Boolean queryInstalledAsUser(")
assert "return null;" in query
assert "result instanceof Boolean ? (Boolean) result : null" in query
assert "Boolean.FALSE.equals(queryInstalledAsUser" in uninstall
single_start = main_ui.index("private void confirmUninstallClone(")
single_end = main_ui.index("private void confirmBatchUninstall(", single_start)
single = main_ui[single_start:single_end]
assert "EngineOperationQueue.submit(" in single
assert "Engine.uninstallClone(item.packageName, item.userId)" in single
assert "repository.removeClone(item.packageName, item.userId" in single
assert single.index("EngineOperationQueue.submit(") < single.index("Engine.uninstallClone(item.packageName, item.userId)") < single.index("repository.removeClone(item.packageName, item.userId")
assert "EngineOperationQueue.submit(" in main_ui
print("Clone uninstall requires explicit Engine absence verification and executes off the UI thread: PASS")

settings = Path("app/src/main/java/com/veyravault/space/ui/SettingsHubActivity.java").read_text(encoding="utf-8")
assert "Backup & Restore" in settings
assert "پشتیبان‌گیری و بازیابی داده‌ها" in settings
assert "not active yet" in settings
print("Future Backup & Restore placeholder remains non-operational and non-destructive: PASS")
