#!/usr/bin/env python3
"""Guard tri-state, user-confirmed, non-destructive pending reservation recovery."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = (ROOT / "app/src/main/java/com/veyravault/space/core/Engine.java").read_text(encoding="utf-8")
ACTIVITY = (ROOT / "app/src/main/java/com/veyravault/space/ui/PendingReservationsActivity.java").read_text(encoding="utf-8")
SETTINGS = (ROOT / "app/src/main/java/com/veyravault/space/ui/SettingsHubActivity.java").read_text(encoding="utf-8")
MANIFEST = (ROOT / "app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")
TEST = (ROOT / "app/src/androidTest/java/com/veyravault/space/core/AsyncCloneRepositoryInstrumentationTest.java").read_text(encoding="utf-8")


def method_body(source: str, signature: str) -> str:
    start = source.index(signature)
    brace = source.index("{", start)
    depth = 0
    for index in range(brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[brace + 1:index]
    raise AssertionError("Unclosed method: " + signature)


# The Engine query must preserve true/false/null as three distinct states.
for state in ("INSTALLED", "ABSENT", "UNKNOWN"):
    assert " " + state in ENGINE
mapping = method_body(ENGINE, "static CloneInstallState classifyInstalledQueryResult(")
assert "installed == null" in mapping and "CloneInstallState.UNKNOWN" in mapping
assert "CloneInstallState.INSTALLED" in mapping and "CloneInstallState.ABSENT" in mapping
query_state = method_body(ENGINE, "public static CloneInstallState getCloneInstallState(")
assert "queryInstalledAsUser(pkg, userId)" in query_state
assert "CloneInstallState.UNKNOWN" in query_state
absence = method_body(ENGINE, "public static boolean isCloneConfirmedAbsent(")
assert "CloneInstallState.ABSENT" in absence

# Diagnostics must only read reservations and Engine state; it must never uninstall,
# clear app data, create a clone record, or silently repair an orphan.
assert "repository.loadPendingReservations" in ACTIVITY
assert "Engine.getCloneInstallState" in ACTIVITY
for forbidden in (
    "Engine.uninstallClone", "Engine.clearCloneData", "CloneStore.removeClone",
    "repository.commitReservedClone", "CloneStore.saveAll",
):
    assert forbidden not in ACTIVITY, forbidden

on_create = method_body(ACTIVITY, "protected void onCreate(")
assert "refreshReservations()" in on_create
assert "releaseReservationAfterEngineAbsence" not in on_create
refresh = method_body(ACTIVITY, "private void refreshReservations(")
assert "repository.loadPendingReservations" in refresh
assert "repository.releaseReservationAfterEngineAbsence" not in refresh

# A manual release always has a confirmation dialog and a fresh Engine query immediately
# before the repository release call. INSTALLED and UNKNOWN both retain the reservation.
release = method_body(ACTIVITY, "private void confirmAndRelease(")
assert "setPositiveButton" in release
assert "Engine.getCloneInstallState" in release
assert "latest != Engine.CloneInstallState.ABSENT" in release
assert release.index("latest != Engine.CloneInstallState.ABSENT") < release.index(
    "repository.releaseReservationAfterEngineAbsence(reservation, true"
)

# The screen is reachable from Settings and is not externally exported.
assert "PendingReservationsActivity.class" in SETTINGS
assert 'android:name=".ui.PendingReservationsActivity" android:exported="false"' in MANIFEST

for test_name in (
    "engineInstallStateMappingPreservesInstalledAbsentAndUnknown",
    "pendingReservationDiagnosticsAreStrictAndReadOnly",
):
    assert test_name in TEST, test_name

print("Pending reservation diagnostics tri-state contract: PASS")
print("Manual release rechecks Engine absence and remains non-destructive: PASS")
print("Installed/unknown reservations stay blocked: PASS")
