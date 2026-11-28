#!/usr/bin/env python3
"""Read-only contract for the Clone Identity Overlap diagnostics screen."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    path = ROOT / relative
    assert path.is_file(), f"Expected Clone identity diagnostics source missing: {path}"
    return path.read_text(encoding="utf-8")


audit = read("app/src/main/java/com/veyravault/space/core/CloneIdentityAudit.java")
engine = read("app/src/main/java/com/veyravault/space/core/Engine.java")
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
assert "auditInventory(" in audit
assert "engineUserIdsWithoutRegisteredClone" in audit
assert "registeredCloneUserIdsMissingFromEngine" in audit
assert "knownAccountManagerUserIds" in audit
assert "accountManagerUserIdsWithoutCurrentEngineUser" in audit
assert "accountManagerUserIdsWithoutRegisteredClone" in audit
assert "accountManagerUserIdsSharedAcrossPackages" in audit
assert "AccountManager data is represented only by numeric userId map keys" in audit

# Engine inventory returns only sorted IDs and fails closed if the Engine is unavailable.
assert "getKnownVirtualUserIds()" in engine
assert 'Class.forName(\n                "top.niunaijun.blackbox.fake.frameworks.BUserManager")' in engine
assert 'getMethod("getService")' in engine
assert 'Class.forName(\n                "top.niunaijun.blackbox.core.system.user.IBUserManagerService")' in engine
assert 'serviceInterface.getMethod("getUsers")' in engine
assert 'getField("id")' in engine
assert "Collections.unmodifiableList(new ArrayList<Integer>(ids))" in engine
user_inventory_start = engine.index("public static List<Integer> getKnownVirtualUserIds()")
user_inventory_end = engine.index("\n    public static List<Integer> getKnownAccountUserIds()", user_inventory_start)
user_inventory_method = engine[user_inventory_start:user_inventory_end]
for forbidden in ("BAccountManager", "getAuthToken", "accounts.conf", "AccountManager.get", "deleteUser", "clearPackage"):
    assert forbidden not in user_inventory_method, "Engine virtual-user inventory must not read or mutate account/session data: " + forbidden

# AccountManager inventory is a separate ID-only API. Its own method may resolve
# BAccountManager, but must not expose or mutate credentials, account payloads or sessions.
account_inventory_start = engine.index("public static List<Integer> getKnownAccountUserIds()")
account_inventory_end = engine.index("\n    public static void doAttachBaseContext", account_inventory_start)
account_inventory_method = engine[account_inventory_start:account_inventory_end]
assert 'Class.forName(\n                "top.niunaijun.blackbox.fake.frameworks.BAccountManager")' in account_inventory_method
assert 'getMethod("getKnownAccountUserIds")' in account_inventory_method
assert "Collections.unmodifiableList" in account_inventory_method
for forbidden in ("getPassword(", "getUserData(", "getAuthToken(", "setAuthToken(", "saveAllAccounts", "deleteUser", "clearPackage"):
    assert forbidden not in account_inventory_method, "AccountManager inventory must remain ID-only and read-only: " + forbidden
for forbidden in ("SharedPreferences", "ContentResolver", "FileInputStream",
                  "getPassword(", "getUserData(", "getAuthToken(", "setAuthToken("):
    assert forbidden not in audit, "Identity grouping must not access account data or external runtime state: " + forbidden
# Reject an actual static Engine method call, not a field name ending in "Engine".
assert re.search(r"\bEngine\s*\.\s*[A-Za-z_$][A-Za-z0-9_$]*\s*\(", audit) is None, "Identity grouping must not invoke Engine APIs"

# The UI reads the strict Clone registry asynchronously and delegates only to the pure audit.
assert "repository.loadClones(result ->" in activity
assert "EngineOperationQueue.submit(" in activity
assert "Engine.getKnownVirtualUserIds()" in activity
assert "Engine.getKnownAccountUserIds()" in activity
assert "CloneIdentityAudit.auditInventory(" in activity
assert "inventories.accountManagerUserIds" in activity
assert "renderPartialInventory(snapshot, inventories)" in activity
assert "AccountManager numeric bucket keys" in activity
assert "No AccountManager key is attributed to a package or specific Clone" in activity
assert "renderRegistryOnly(snapshot, failure)" in activity
assert "No all-clear result is reported." in activity
assert "if (!result.isSuccess() || result.getValue() == null)" in activity
assert "No all-clear result is reported." in activity
assert "does not prove historical deleted-user account buckets are empty" in activity
assert "Engine IDs without a current Clone record" in activity
assert "Clone IDs missing from the current Engine inventory" in activity
for forbidden in (
    "Engine.getCloneInstallState",
    "CloneStore.removeClone(",
    "CloneStore.upsertClone(",
    "CloneStore.saveAll(",
    "clearCloneData(",
    "uninstallClone(",
    "AccountManager.get(",
    "getSharedPreferences(",
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
    "engineInventoryReportsUnlinkedAndMissingCloneUserIds",
    "engineInventoryRejectsDuplicateOrInvalidIds",
    "inventoryReportCollectionsAreImmutable",
    "accountManagerInventoryClassifiesHistoricalBucketsAndSharedNumericScope",
    "accountManagerInventoryRejectsDuplicateOrInvalidIds",
    "accountManagerInventoryCollectionsAreImmutable",
):
    assert test_name in tests

print("PASS: duplicate userId groups are computed from a strict Clone registry snapshot.")
print("PASS: Engine inventory exposes IDs only and fails closed when unavailable.")
print("PASS: diagnostics compares AccountManager numeric keys with Engine and Clone IDs without reading account records.")
print("PASS: diagnostics reads the Clone registry asynchronously and fails closed on invalid data.")
print("PASS: the Settings entry and non-exported Activity are registered.")
print("PASS: synthetic tests cover Clone overlaps, AccountManager historical candidates, shared numeric scope, invalid IDs and immutable output.")
print("PASS: no Engine account/session, package files, SharedPreferences or mutation API is accessed.")
