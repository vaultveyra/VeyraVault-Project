#!/usr/bin/env python3
"""Test the build-time hardening patch against isolated pinned-Engine source fixtures."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREPARE_PATH = ROOT / "scripts" / "prepare_workspace.py"
SPEC = importlib.util.spec_from_file_location("veyravault_prepare_stage_825", PREPARE_PATH)
assert SPEC is not None and SPEC.loader is not None
prepare = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prepare)

BASE = Path("Bcore/src/main/java/top/niunaijun/blackbox")
FIXTURES = {
    "core/system/pm/installer/RemoveUserExecutor.java": """package top.niunaijun.blackbox.core.system.pm.installer;

import top.niunaijun.blackbox.core.env.BEnvironment;
import top.niunaijun.blackbox.core.system.pm.BPackageSettings;
import top.niunaijun.blackbox.entity.pm.InstallOption;
import top.niunaijun.blackbox.utils.FileUtils;


public class RemoveUserExecutor implements Executor {

    @Override
    public int exec(BPackageSettings ps, InstallOption option, int userId) {
        String packageName = ps.pkg.packageName;
        
        FileUtils.deleteDir(BEnvironment.getDataDir(packageName, userId));
        FileUtils.deleteDir(BEnvironment.getDeDataDir(packageName, userId));
        FileUtils.deleteDir(BEnvironment.getExternalDataDir(packageName, userId));
        return 0;
    }
}
""",
    "core/system/pm/installer/RemoveAppExecutor.java": """package top.niunaijun.blackbox.core.system.pm.installer;

import top.niunaijun.blackbox.core.env.BEnvironment;
import top.niunaijun.blackbox.core.system.pm.BPackageSettings;
import top.niunaijun.blackbox.entity.pm.InstallOption;
import top.niunaijun.blackbox.utils.FileUtils;


public class RemoveAppExecutor implements Executor {
    @Override
    public int exec(BPackageSettings ps, InstallOption option, int userId) {
        FileUtils.deleteDir(BEnvironment.getAppDir(ps.pkg.packageName));
        return 0;
    }
}
""",
    "core/system/pm/installer/CreateUserExecutor.java": """package top.niunaijun.blackbox.core.system.pm.installer;

import top.niunaijun.blackbox.core.env.BEnvironment;
import top.niunaijun.blackbox.core.system.pm.BPackageSettings;
import top.niunaijun.blackbox.entity.pm.InstallOption;
import top.niunaijun.blackbox.utils.FileUtils;


public class CreateUserExecutor implements Executor {

    @Override
    public int exec(BPackageSettings ps, InstallOption option, int userId) {
        String packageName = ps.pkg.packageName;
        FileUtils.deleteDir(BEnvironment.getDataLibDir(packageName, userId));

        
        FileUtils.mkdirs(BEnvironment.getDataDir(packageName, userId));
        FileUtils.mkdirs(BEnvironment.getDataCacheDir(packageName, userId));
        FileUtils.mkdirs(BEnvironment.getDataFilesDir(packageName, userId));
        FileUtils.mkdirs(BEnvironment.getDataDatabasesDir(packageName, userId));
        FileUtils.mkdirs(BEnvironment.getDeDataDir(packageName, userId));









        return 0;
    }
}
""",
    "core/system/pm/BPackageInstallerService.java": """package top.niunaijun.blackbox.core.system.pm;

public class BPackageInstallerService {
    public int uninstallPackageAsUser(BPackageSettings ps, boolean removeApp, int userId) {
        List<Executor> executors = new ArrayList<>();
        if (removeApp) {
            
            executors.add(new RemoveAppExecutor());
        }
        
        executors.add(new RemoveUserExecutor());
        InstallOption option = ps.installOption;
        for (Executor executor : executors) {
            int exec = executor.exec(ps, option, userId);
            if (exec != 0) {
                return exec;
            }
        }
        return 0;
    }

    public int clearPackage(BPackageSettings ps, int userId) {
        return 0;
    }
}
""",
    "core/system/pm/BPackageManagerService.java": """package top.niunaijun.blackbox.core.system.pm;

public class BPackageManagerService {
    public void uninstallPackageAsUser(String packageName, int userId) {
                int i = BPackageInstallerService.get().uninstallPackageAsUser(ps, removeApp, userId);
                if (i < 0) {
                    
                }

        if (removeApp) {
            mSettings.removePackage(packageName);
        } else {
            ps.removeUser(userId);
            ps.save();
        }
        onPackageUninstalled(packageName, removeApp, userId);
    }

    public void uninstallPackage(String packageName) {
        for (Integer userId : ps.getUserIds()) {
                        int i = BPackageInstallerService.get().uninstallPackageAsUser(ps, true, userId);
                        if (i < 0) {
                            continue;
                        }
            onPackageUninstalled(packageName, true, userId);
        }
        mSettings.removePackage(packageName);
        mComponentResolver.removeAllComponents(ps.pkg);
    }

    public void clearPackage(String packageName, int userId) {
        int i = BPackageInstallerService.get().clearPackage(ps, userId);
    }
}
""",
}


class EngineCleanupHardeningTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for relative, content in FIXTURES.items():
            path = self.root / BASE / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def read(self, relative):
        return (self.root / BASE / relative).read_text(encoding="utf-8")

    def test_patch_checks_directory_absence_and_recreation(self):
        prepare.harden_clone_cleanup_semantics(str(self.root))
        remove_user = self.read("core/system/pm/installer/RemoveUserExecutor.java")
        remove_app = self.read("core/system/pm/installer/RemoveAppExecutor.java")
        create_user = self.read("core/system/pm/installer/CreateUserExecutor.java")
        installer = self.read("core/system/pm/BPackageInstallerService.java")
        manager = self.read("core/system/pm/BPackageManagerService.java")

        self.assertIn("import java.io.File;", remove_user)
        self.assertEqual(remove_user.count("directory.exists()"), 1)
        self.assertIn("BEnvironment.getDataDir(packageName, userId)", remove_user)
        self.assertIn("BEnvironment.getDeDataDir(packageName, userId)", remove_user)
        self.assertIn("BEnvironment.getExternalDataDir(packageName, userId)", remove_user)
        self.assertIn("BEnvironment.getExternalObbDir(packageName, userId)", remove_user)
        self.assertIn("File[] dataRoots", remove_user)
        self.assertIn("if (!isSafeDirectoryPath(dataRoots[i], directory))", remove_user)
        self.assertIn("FileUtils.isSymlink(ancestor)", remove_user)
        self.assertIn("if (appDirectory.exists())", remove_app)
        self.assertIn("if (dataLibraryDirectory.exists())", create_user)
        self.assertIn("BEnvironment.getExternalObbDir(packageName, userId)", create_user)
        self.assertIn("if (!directory.isDirectory() && !directory.mkdirs() && !directory.isDirectory())", create_user)
        self.assertLess(installer.index("executors.add(new RemoveUserExecutor())"),
                        installer.index("executors.add(new RemoveAppExecutor())"))
        self.assertIn("if (cleanupResult != 0) {\n                    return;", manager)
        self.assertIn("VEYRAVAULT_KEEP_ALL_CLONE_METADATA_ON_BULK_CLEANUP_FAILURE", manager)
        self.assertIn("throw new IllegalStateException(", manager)

    def test_patch_is_idempotent(self):
        prepare.harden_clone_cleanup_semantics(str(self.root))
        before = {relative: self.read(relative) for relative in FIXTURES}
        prepare.harden_clone_cleanup_semantics(str(self.root))
        after = {relative: self.read(relative) for relative in FIXTURES}
        self.assertEqual(before, after)

    def test_unexpected_pinned_source_fails_without_partially_writing_other_files(self):
        original_remove_user = self.read("core/system/pm/installer/RemoveUserExecutor.java")
        changed = self.root / BASE / "core/system/pm/BPackageManagerService.java"
        changed.write_text("package unexpected; class Changed {}", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "no longer matches|unexpected|verification failed"):
            prepare.harden_clone_cleanup_semantics(str(self.root))
        self.assertEqual(self.read("core/system/pm/installer/RemoveUserExecutor.java"), original_remove_user)



# Engine absence requires all package/user data roots to be absent and inspectable.
ENGINE = (ROOT / "app/src/main/java/com/veyravault/space/core/Engine.java").read_text(encoding="utf-8")
guard_start = ENGINE.index("private static boolean isDirectoryConfirmedAbsent(")
state_start = ENGINE.index("private static boolean areCloneDataDirectoriesAbsent(", guard_start)
state_end = ENGINE.index("static CloneInstallState classifyInstallStateWithDataCheck(", state_start)
absence_guard = ENGINE[state_start:state_end]
classifier_start = state_end
query_start = ENGINE.index("public static CloneInstallState getCloneInstallState(", classifier_start)
classifier = ENGINE[classifier_start:query_start]
query_end = ENGINE.index("public static boolean isCloneConfirmedAbsent(", query_start)
query = ENGINE[query_start:query_end]
uninstall_start = ENGINE.index("public static boolean uninstallClone(")
uninstall_end = ENGINE.index("public static boolean isGmsInstalled(", uninstall_start)
uninstall = ENGINE[uninstall_start:uninstall_end]
directory_guard = ENGINE[guard_start:state_start]

for required_path in (
    "BEnvironment.getDataDir(pkg, userId)",
    "BEnvironment.getDeDataDir(pkg, userId)",
    "BEnvironment.getExternalDataDir(pkg, userId)",
    "BEnvironment.getExternalObbDir(pkg, userId)",
):
    assert required_path in absence_guard, f"Missing package/user data guard: {required_path}"
assert "BEnvironment.getAppDir" not in absence_guard, (
    "Shared package APK storage must not be treated as per-user residue."
)
assert "canonicalDirectory.getPath().startsWith(rootPrefix)" in directory_guard
assert "FileUtils.isSymlink(directory)" in directory_guard
assert "FileUtils.isSymlink(ancestor)" in directory_guard
assert "canonicalDirectory.exists()" in directory_guard
assert "state != CloneInstallState.ABSENT" in query
assert "return state;" in query
assert "areCloneDataDirectoriesAbsent(pkg, userId)" in query
assert "CloneInstallState.UNKNOWN" in query
assert "dataDirectoriesAbsent ? CloneInstallState.ABSENT : CloneInstallState.UNKNOWN" in classifier
assert "Boolean.FALSE.equals(queryInstalledAsUser(pkg, userId))" in uninstall
assert "areCloneDataDirectoriesAbsent(pkg, userId)" in uninstall

print("PASS: ABSENT requires Engine metadata absence plus all internal, DE, Android/data and OBB roots absent.")
print("PASS: Per-user inspection excludes the package-shared APK directory.")
print("PASS: Inaccessible, out-of-root and symlink-escaped paths remain UNKNOWN.")

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(EngineCleanupHardeningTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("Stage 8.25 pinned Engine cleanup failure semantics patch: PASS")
