#!/usr/bin/env python3
"""Read-only contract for the Clone Identity Overlap diagnostics screen."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    path = ROOT / relative
    assert path.is_file(), f"Expected Clone identity diagnostics source missing: {path}"
    return path.read_text(encoding="utf-8")


audit = read("app/src/main/java/com/veyravault/space/core/CloneIdentityAudit.java")
activity = read("app/src/main/java/com/veyravault/space/ui/CloneIdentityDiagnosticsActivity.java")
settings = read("app/src/main/java/com/veyravault/space/ui/SettingsHubActivity.java")
manifest = read("app/src/main/AndroidManifest.xml")
tests = read("app/src/androidTest/java/com/veyravault/space/core/CloneIdentityAuditInstrumentationTest.java")

# The helper must be a pure transformation of the already-read registry snapshot.
assert "findCrossPackageCollisions(" in audit
assert "new TreeMap<Integer, Map<String, CloneIdentity>>()" in audit
assert "group.getValue().size() <= 1" in audit
assert "Collections.unmodifiableList" in audit
assert "Collections.unmodifiableList(new ArrayList<>(clones))" in audit
for forbidden in ("SharedPreferences", "ContentResolver", "AccountManager", "Engine.", "FileInputStream"):
    assert forbidden not in audit, "Identity grouping must not access external/runtime state: " + forbidden

# The UI reads the strict Clone registry asynchronously and delegates only to the pure audit.
assert "repository.loadClones(result ->" in activity
assert "CloneIdentityAudit.findCrossPackageCollisions(snapshot)" in activity
assert "if (!result.isSuccess() || result.getValue() == null)" in activity
assert "No current cross-package numeric userId overlap was found." in activity
assert "historical Engine account records are absent" in activity
for forbidden in (
    "Engine.getCloneInstallState",
    "EngineOperationQueue",
    "CloneStore.removeClone(",
    "CloneStore.upsertClone(",
    "CloneStore.saveAll(",
    "clearCloneData(",
    "uninstallClone(",
    "AccountManager",
    "SharedPreferences",
):
    assert forbidden not in activity, "Diagnostics screen must remain read-only: " + forbidden

assert "CloneIdentityDiagnosticsActivity.class" in settings
assert '<activity android:name=".ui.CloneIdentityDiagnosticsActivity" android:exported="false" />' in manifest

# Synthetic helper tests cover cross-package overlaps, normal same-package spaces,
# corrupt duplicate composite identities and immutable report output.
for test_name in (
    "reportsOnlyDifferentPackagesSharingTheSameNumericUserId",
    "returnsNoCollisionForOnePackageOrUniqueNumericIds",
    "rejectsDuplicateCompositeIdentityInsteadOfHidingCorruptRegistryData",
    "collisionReportIsImmutable",
):
    assert test_name in tests

print("PASS: duplicate userId groups are computed from a supplied Clone registry snapshot only.")
print("PASS: diagnostics reads the Clone registry asynchronously and fails closed on invalid data.")
print("PASS: the Settings entry and non-exported Activity are registered.")
print("PASS: synthetic tests cover overlap, no-overlap, invalid identity and immutable output.")
print("PASS: no Engine account/session, package files, SharedPreferences or mutation API is accessed.")
