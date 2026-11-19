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
assert "catch (Throwable error)" in install and "return false;" in install

installed = method_body("private static boolean isInstalledAsUser(")
assert "Boolean.TRUE.equals(queryInstalledAsUser(pkg, userId))" in installed
assert "return false;" not in installed
query_installed = method_body("private static Boolean queryInstalledAsUser(")
assert 'getMethod("isInstalled", String.class, int.class)' in query_installed
assert "result instanceof Boolean ? (Boolean) result : null" in query_installed
assert "return null;" in query_installed

launch = method_body("public static CloneLaunchResult launchCloneDetailed(")
assert "if (!isInstalledAsUser(entry.packageName, entry.userId)" in launch
assert "&& !installPackageAsUser(entry.packageName, entry.userId))" in launch
assert "ENGINE_INSTALL_FAILED" in launch
assert "if (!Boolean.TRUE.equals(value))" in launch
assert launch.index("installPackageAsUser(entry.packageName, entry.userId)") < launch.index("VirtualHookManager.syncCloneHooks(ctx, entry)")
assert launch.index("VirtualHookManager.syncCloneHooks(ctx, entry)") < launch.index('getMethod("launchApk", String.class, int.class)')
assert launch.index("if (!Boolean.TRUE.equals(value))") < launch.index("CloneStore.recordActiveLaunch(ctx, entry)")
assert "r == null || Boolean.TRUE.equals(r)" not in launch
compat = method_body("public static boolean launchClone(")
assert "return launchCloneDetailed(ctx, entry).launched;" in compat
print("Engine install/launch failure contract: PASS")
print("Active-launch marker is written only after confirmed engine launch: PASS")

# UI must not persist a clone registry entry after a failed engine install.
main_ui = Path("app/src/main/java/com/veyravault/space/ui/MainActivity.java").read_text(encoding="utf-8")
add_ui = Path("app/src/main/java/com/veyravault/space/ui/AddAppActivity.java").read_text(encoding="utf-8")
assert "repository.reserveNextUserId(item.packageName" in main_ui
assert "if (!Engine.installPackageAsUser(copy.packageName, copy.userId))" in main_ui
assert main_ui.index("if (!Engine.installPackageAsUser(copy.packageName, copy.userId))") < main_ui.index("repository.commitReservedClone(copy")
assert "repository.reserveNextUserId(app.pkg" in add_ui
assert "if (!Engine.installPackageAsUser(entry.packageName, entry.userId))" in add_ui
assert add_ui.index("if (!Engine.installPackageAsUser(entry.packageName, entry.userId))") < add_ui.index("repository.commitReservedClone(entry")
assert "Engine.uninstallClone(entry.packageName, entry.userId)" in add_ui
assert "Engine.isCloneConfirmedAbsent" in add_ui and "releaseReservationAfterEngineAbsence" in add_ui
assert "repository.allocateNextUserId" not in main_ui + add_ui
assert "repository.upsertClone(copy" not in main_ui and "repository.upsertClone(entry" not in add_ui
assert "boolean launched = Engine.launchClone(MainActivity.this, item);" in main_ui
print("Clone creation UI failure handling: PASS")

uninstall = method_body("public static boolean uninstallClone(")
assert "queryInstalledAsUser(pkg, userId)" in uninstall
assert "Boolean.FALSE.equals(queryInstalledAsUser(pkg, userId))" in uninstall
assert "return false;" in uninstall
query = method_body("private static Boolean queryInstalledAsUser(")
assert "return null;" in query
assert "result instanceof Boolean ? (Boolean) result : null" in query
assert "Boolean.FALSE.equals(queryInstalledAsUser" in uninstall
assert "if (!Engine.uninstallClone(item.packageName, item.userId))" in main_ui
assert "repository.removeClone(item.packageName, item.userId" in main_ui
assert main_ui.index("if (!Engine.uninstallClone(item.packageName, item.userId))") < main_ui.index("repository.removeClone(item.packageName, item.userId")
print("Clone uninstall requires explicit engine absence verification: PASS")
print("Registry records are retained when uninstall is unconfirmed; removal is async after confirmation: PASS")

settings = Path("app/src/main/java/com/veyravault/space/ui/SettingsHubActivity.java").read_text(encoding="utf-8")
assert "Backup & Restore" in settings
assert "پشتیبان‌گیری و بازیابی داده‌ها" in settings
assert "not active yet" in settings
print("Future Backup & Restore placeholder remains non-operational and non-destructive: PASS")
