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
assert "if (core == null) return false;" in install
assert "if (res == null) return false;" in install
assert "success.getBoolean(res)" in install
assert "catch (Throwable t)" in install and "return false;" in install

installed = method_body("private static boolean isInstalledAsUser(")
assert 'getMethod("isInstalled", String.class, int.class)' in installed
assert "Boolean.TRUE.equals(result)" in installed
assert "return false;" in installed

launch = method_body("public static boolean launchClone(")
assert "if (!isInstalledAsUser(entry.packageName, entry.userId)" in launch
assert "&& !installPackageAsUser(entry.packageName, entry.userId))" in launch
assert "return false;" in launch
assert "return Boolean.TRUE.equals(r);" in launch
assert "r == null || Boolean.TRUE.equals(r)" not in launch
assert launch.index("installPackageAsUser(entry.packageName, entry.userId)") < launch.index("CloneStore.recordActiveLaunch(ctx, entry)")
assert launch.index("CloneStore.recordActiveLaunch(ctx, entry)") < launch.index("VirtualHookManager.syncCloneHooks(ctx, entry)")
print("Engine install/launch failure contract: PASS")

# UI must not persist a clone registry entry after a failed engine install.
main_ui = Path("app/src/main/java/com/veyravault/space/ui/MainActivity.java").read_text(encoding="utf-8")
add_ui = Path("app/src/main/java/com/veyravault/space/ui/AddAppActivity.java").read_text(encoding="utf-8")
assert "if (!Engine.installPackageAsUser(copy.packageName, copy.userId))" in main_ui
assert main_ui.index("if (!Engine.installPackageAsUser(copy.packageName, copy.userId))") < main_ui.index("CloneStore.upsertClone(MainActivity.this, copy)")
assert "if (!Engine.installPackageAsUser(e.packageName, e.userId))" in add_ui
assert add_ui.index("if (!Engine.installPackageAsUser(e.packageName, e.userId))") < add_ui.index("CloneStore.upsertClone(this, e)")
assert "boolean launched = Engine.launchClone(MainActivity.this, item);" in main_ui
print("Clone creation UI failure handling: PASS")
