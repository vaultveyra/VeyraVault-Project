from pathlib import Path

root = Path("app/src/main/java/com/veyravault/space")
source = (root / "ui/DashboardActivity.java").read_text(encoding="utf-8")
repository = (root / "core/AsyncCloneRepository.java").read_text(encoding="utf-8")
resolver = (root / "core/ProfileResolver.java").read_text(encoding="utf-8")
workflow = Path(".github/workflows/build-and-audit.yml").read_text(encoding="utf-8")

# Host network reporting must use Android's observed connectivity state and be labeled as host-only.
for marker in (
    "ConnectivityManager",
    "getActiveNetwork()",
    "getNetworkCapabilities(active)",
    "NetworkCapabilities.TRANSPORT_VPN",
    "NetworkCapabilities.TRANSPORT_WIFI",
    "NetworkCapabilities.TRANSPORT_CELLULAR",
    "NetworkCapabilities.NET_CAPABILITY_VALIDATED",
    "Host network:",
    "This alone does not prove each Clone traffic route",
):
    assert marker in source, f"Missing verified host-network behavior: {marker}"

# The Dashboard must not infer or fabricate a public IP.
assert "Public IP" in source
assert "Not checked" in source
assert "has not sent a public-IP lookup request" in source
assert "api.ipify" not in source.lower()
assert "8.8.8.8" not in source

# Global device and carrier fields are shown only as stored metadata, never as applied identity.
for marker in (
    "loadGlobalDeviceMetadata",
    "loadGlobalEnvironment",
    "Saved brand/model:",
    "Saved country code:",
    "Saved operator code:",
    "metadata only; the pinned engine does not apply them",
):
    assert marker in source, f"Missing Global metadata disclosure: {marker}"

# Effective profile reads remain asynchronous and the last-launch marker must match the
# strict Clone registry's composite packageName + userId identity before Clone data is shown.
for marker in (
    "loadEffectiveProfileSummary",
    "repository.loadGlobalProfile",
    "repository.loadLastActiveLaunch",
    "repository.loadCloneProfile(active.packageName, active.userId",
    "active.packageName.equals(entry.packageName)",
    "active.userId == entry.userId",
    "ProfileResolver.resolve(",
    "ProfileRuntimeApplier.systemFallback()",
    "effective.localeSource",
    "effective.timeZoneSource",
    "effective.locationEnabledSource",
    "Clone → Global → System",
):
    assert marker in source, f"Missing validated effective-profile behavior: {marker}"

assert "ProfileStore." not in source, "Dashboard must use the async repository facade"
assert "CloneStore.save" not in source
assert "CloneStore.remove" not in source
assert "CloneStore.clear" not in source
assert "Engine.stopClone" not in source
assert "Engine.clearCloneData" not in source
assert "Engine.uninstallClone" not in source

assert "public void loadLastActiveLaunch" in repository
assert "public void loadGlobalProfile" in repository
assert "public void loadCloneProfile" in repository
assert "public static ResolvedProfile resolve(" in resolver
assert "scripts/test_dashboard_verified_environment_summary.py" in workflow

print("PASS: Dashboard reports observed host network only, discloses unsupported device metadata, validates last Clone identity, and resolves supported profile fields without external IP fabrication or data mutation.")
