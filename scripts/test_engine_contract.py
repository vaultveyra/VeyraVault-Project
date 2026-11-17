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
print("Engine install/launch failure contract: PASS")
