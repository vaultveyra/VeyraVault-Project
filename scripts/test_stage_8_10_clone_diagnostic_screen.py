#!/usr/bin/env python3
"""Read-only, per-Clone diagnostics contract for Stage 8.10."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
manager = (root / "app/src/main/java/com/veyravault/space/core/CompatibilityManager.java").read_text(encoding="utf-8")
gms = (root / "app/src/main/java/com/veyravault/space/core/GmsSupportManager.java").read_text(encoding="utf-8")
activity = (root / "app/src/main/java/com/veyravault/space/ui/AppCompatibilityDiagnosticsActivity.java").read_text(encoding="utf-8")
entry_activity = (root / "app/src/main/java/com/veyravault/space/ui/CompatibilityReportActivity.java").read_text(encoding="utf-8")
manifest = (root / "app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")
doc = (root / "docs/STAGE_8_10_APP_COMPATIBILITY_DIAGNOSTICS.md").read_text(encoding="utf-8")

for marker in (
    "Engine.getCloneInstallState(clone.packageName, clone.userId)",
    "GmsSupportManager.getGmsState(clone.userId)",
    "splitSourceDirs",
    "new ZipFile(path)",
    "Build.SUPPORTED_ABIS",
    "WebView.getCurrentWebViewPackage()",
    "Environment.isExternalStorageManager()",
    "launch_observation",
    "This report did not launch the target app",
    "formatCloneReport",
):
    assert marker in manager, marker

assert "enum GmsState { INSTALLED, ABSENT, UNKNOWN }" in gms
assert "result instanceof Boolean" in gms
assert "return GmsState.UNKNOWN" in gms
assert "getGmsState(userId) == GmsState.INSTALLED" in gms

collect = manager[manager.index("public static List<CheckItem> collectClone"):
                 manager.index("/** Formats only the bounded CheckItem values above")]
for forbidden in (
    "installPackageAsUser(", "uninstallClone(", "clearCloneData(",
    "setGmsEnabled(", "setLocation(", "setPattern(",
    "CloneStore.removeClone(", "CloneStore.upsertClone(",
    "ProfileStore.save", "clone.latitude", "clone.longitude",
    "deniedPermissions",
):
    assert forbidden not in collect, forbidden

assert "AsyncCloneRepository.getInstance(getApplicationContext()).loadClones" in activity
assert "CompatibilityManager.formatCloneReport(getApplicationContext(), clone)" in activity
assert "diagnosticsWorker.execute" in activity
assert "Intent.ACTION_SEND" in activity
assert "Intent.EXTRA_TEXT" in activity
assert "Intent.createChooser" in activity
assert "createLanguageAction(fa)" in activity
assert "createImmediateLockSwitch(fa)" in activity
report_formatter = manager[manager.index("public static String formatCloneReport"):]
assert 'report.append("Space:")' not in report_formatter
assert "clone.userId" not in report_formatter
for forbidden in ("removeClone(", "upsertClone(", "saveCloneProfile(", "clearCloneData(",
                  "installPackageAsUser(", "uninstallClone("):
    assert forbidden not in activity, forbidden

assert "AppCompatibilityDiagnosticsActivity" in entry_activity
assert 'android:name=".ui.AppCompatibilityDiagnosticsActivity" android:exported="false"' in manifest
assert "app-private" in doc.lower()
assert "not a physical-device reproduction" in doc.lower()

print("Stage 8.10: per-Clone report reads Engine and package metadata without modifying Clone state: PASS")
print("Stage 8.10: split APK and native ABI metadata inspection is read-only: PASS")
print("Stage 8.10: GMS UNKNOWN is distinct from confirmed ABSENT: PASS")
print("Stage 8.10: report omits private/session data and shares only on explicit user action: PASS")
