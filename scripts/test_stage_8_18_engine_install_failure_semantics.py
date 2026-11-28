#!/usr/bin/env python3
"""Guard and report the pinned Engine's known install-failure semantics.

This is a source-level audit, not a production fix. It locks the reviewed
control-flow facts so an upstream/generated Engine change requires an
intentional re-audit before the runtime integration design advances.
"""
from pathlib import Path
import re

ROOT = Path("build_workspace")
ENGINE_ROOT = ROOT / "Bcore/src/main/java/top/niunaijun/blackbox"

SETTINGS = ENGINE_ROOT / "core/system/pm/Settings.java"
MANAGER = ENGINE_ROOT / "core/system/pm/BPackageManagerService.java"
PACKAGE_SETTINGS = ENGINE_ROOT / "core/system/pm/BPackageSettings.java"
USER_STATE = ENGINE_ROOT / "core/system/pm/BPackageUserState.java"
CREATE_USER = ENGINE_ROOT / "core/system/pm/installer/CreateUserExecutor.java"
CREATE_PACKAGE = ENGINE_ROOT / "core/system/pm/installer/CreatePackageExecutor.java"
CORE = ENGINE_ROOT / "BlackBoxCore.java"
INSTALL_RESULT = ENGINE_ROOT / "entity/pm/InstallResult.java"

for path in (
    SETTINGS, MANAGER, PACKAGE_SETTINGS, USER_STATE,
    CREATE_USER, CREATE_PACKAGE, CORE, INSTALL_RESULT,
):
    assert path.is_file(), f"Pinned Engine source missing; re-audit required: {path}"

settings = SETTINGS.read_text(encoding="utf-8")
manager = MANAGER.read_text(encoding="utf-8")
package_settings = PACKAGE_SETTINGS.read_text(encoding="utf-8")
user_state = USER_STATE.read_text(encoding="utf-8")
create_user = CREATE_USER.read_text(encoding="utf-8")
create_package = CREATE_PACKAGE.read_text(encoding="utf-8")
core = CORE.read_text(encoding="utf-8")
install_result = INSTALL_RESULT.read_text(encoding="utf-8")


def method_body(source: str, signature: str) -> str:
    start = source.find(signature)
    assert start >= 0, f"Method signature changed; review required: {signature}"
    brace = source.find("{", start)
    assert brace >= 0, f"Method body missing: {signature}"
    depth = 0
    for index in range(brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[brace + 1:index]
    raise AssertionError(f"Unclosed method: {signature}")


def block_after(source: str, marker: str) -> str:
    start = source.find(marker)
    assert start >= 0, f"Required control-flow marker changed: {marker}"
    brace = source.find("{", start)
    assert brace >= 0
    depth = 0
    for index in range(brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[brace + 1:index]
    raise AssertionError("Unclosed source block: " + marker)


# 1. Existing package user-state map is aliased into the candidate settings.
get_package = method_body(
    settings,
    "BPackageSettings getPackageLPw(String name, PackageParser.Package aPackage, InstallOption installOption)",
)
assert "origSettings.userState = pkgSettings.userState;" in get_package
assert "new HashMap" not in get_package and "cloneUserState" not in get_package
assert "public BPackageUserState(BPackageUserState state)" in user_state
assert "this.installed = state.installed;" in user_state
print("CONFIRMED: candidate BPackageSettings reuses the prior userState map reference.")

# 2. save() reports failure, but install ignores its boolean return value.
save = method_body(package_settings, "public boolean save()")
assert "return true;" in save and "return false;" in save
install = method_body(
    manager,
    "private InstallResult installPackageAsUserLocked(String file, InstallOption option, int userId)",
)
assert re.search(r"(?m)^\s*bPackageSettings\.save\(\);\s*$", install), (
    "Install caller no longer uses the reviewed unchecked save statement; re-audit"
)
assert not re.search(r"(?m)^\s*(boolean|if|assert)\b[^\n]*bPackageSettings\.save", install)
set_installed = install.find("bPackageSettings.setInstalled(true, userId);")
save_at = install.find("bPackageSettings.save();")
resolver_remove = install.find("mComponentResolver.removeAllComponents(bPackageSettings.pkg);")
resolver_add = install.find("mComponentResolver.addAllComponents(bPackageSettings.pkg);")
scan_at = install.find("mSettings.scanPackage(aPackage.packageName);")
notify_at = install.find("onPackageInstalled(bPackageSettings.pkg.packageName, userId);")
success_return = install.find("return result;", notify_at)
assert -1 not in (set_installed, save_at, resolver_remove, resolver_add, scan_at, notify_at, success_return)
assert set_installed < save_at < resolver_remove < resolver_add < scan_at < notify_at < success_return
assert "public boolean success = true;" in install_result
print("CONFIRMED: unchecked settings-save result can flow through scan/notification to default-success InstallResult.")

# 3. Settings scan catch deletes the package directory and removes only package settings.
update = method_body(settings, "private void updatePackageLP(File app)")
catch = block_after(update, "catch (Throwable e)")
assert "FileUtils.deleteDir(app);" in catch
assert "removePackage(packageName);" in catch
assert "BProcessManagerService.get().killAllByPackageName(packageName);" in catch
assert "onPackageUninstalled(packageName, true, BUserHandle.USER_ALL);" in catch
assert "mComponentResolver.removeAllComponents" not in catch
remove_package = method_body(settings, "public void removePackage(String packageName)")
assert "mPackages.remove(packageName);" in remove_package
print("CONFIRMED: scan failure deletes package files/removes settings; resolver cleanup is not in this catch.")

# 4. Installer mutates user/package paths before new generation publication is proven.
user_exec = method_body(create_user, "public int exec(BPackageSettings ps, InstallOption option, int userId)")
assert "File dataLibraryDirectory = BEnvironment.getDataLibDir(packageName, userId);" in user_exec
assert "FileUtils.deleteDir(dataLibraryDirectory);" in user_exec
assert "if (dataLibraryDirectory.exists())" in user_exec
assert "VEYRAVAULT_VERIFY_CLONE_DATA_RESET" in user_exec
package_exec = method_body(create_package, "public int exec(BPackageSettings ps, InstallOption option, int userId)")
assert "FileUtils.deleteDir(BEnvironment.getAppDir(ps.pkg.packageName));" in package_exec
assert "CreateUserExecutor" in manager or "CreateUserExecutor" in (
    ENGINE_ROOT / "core/system/pm/BPackageInstallerService.java"
).read_text(encoding="utf-8")
print("CONFIRMED: selected user's lib child and shared package directory are deleted by install executors.")

# 5. VeyraVault's current two-argument package-name path uses system-source install flags.
core_install = method_body(
    core,
    "public InstallResult installPackageAsUser(String packageName, int userId)",
)
assert "InstallOption.installBySystem()" in core_install
assert "packageInfo.applicationInfo.sourceDir" in core_install
assert "InstallOption.installByStorage()" not in core_install
print("CONFIRMED: VeyraVault package-name path uses FLAG_SYSTEM source semantics.")

print("Stage 8.18 pinned Engine install failure semantics audit: PASS")
print("Production transaction safety: BLOCKED — source-level hazards are still present.")
print("No runtime patch, CloneStore change, virtual-data mutation, or Engine pin change was made.")
