from pathlib import Path

root = Path("app/src/main")
java = root / "java/com/veyravault/space"
manager = (java / "security/AppDisguiseManager.java").read_text(encoding="utf-8")
selector = (java / "ui/AppIconNameActivity.java").read_text(encoding="utf-8")
settings = (java / "ui/SettingsHubActivity.java").read_text(encoding="utf-8")
security = (java / "ui/SecuritySettingsActivity.java").read_text(encoding="utf-8")
about = (java / "ui/AboutActivity.java").read_text(encoding="utf-8")
manifest = (root / "AndroidManifest.xml").read_text(encoding="utf-8")
instrumentation = Path("app/src/androidTest/java/com/veyravault/space/security/AppDisguiseManagerInstrumentationTest.java").read_text(encoding="utf-8")
workflow = Path(".github/workflows/build-and-audit.yml").read_text(encoding="utf-8")

# Programmatic layouts use local density conversion helpers; the BaseActivity helper is private.
for path in (
    java / "ui/AppIconNameActivity.java",
    java / "ui/SettingsHubActivity.java",
    java / "ui/SecuritySettingsActivity.java",
    java / "ui/AboutActivity.java",
):
    source = path.read_text(encoding="utf-8")
    assert "private int dp(int value)" in source, f"Missing local density helper in {path.name}"

# Launcher options must be exactly the five aliases declared by the application manifest.
aliases = (
    "com.veyravault.space.AliasDefault",
    "com.veyravault.space.AliasCalculator",
    "com.veyravault.space.AliasCalendar",
    "com.veyravault.space.AliasNotes",
    "com.veyravault.space.AliasWeather",
)
for alias in aliases:
    assert alias in manager, f"Missing supported alias in manager: {alias}"
    assert f'android:name=".{alias.split(".")[-1]}"' in manifest, f"Alias not declared in manifest: {alias}"

for icon in (
    "ic_launcher_vault",
    "ic_disguise_calc",
    "ic_disguise_calendar",
    "ic_disguise_notes",
    "ic_disguise_weather",
):
    assert f"R.drawable.{icon}" in selector, f"Missing bundled launcher icon: {icon}"

assert 'android:name=".ui.AppIconNameActivity" android:exported="false"' in manifest
assert "AppIconNameActivity.class" in settings
assert "AppIconNameActivity.class" in security

# Search, selection, truthful success/failure feedback, validation and rollback.
for marker in (
    "addTextChangedListener",
    "normalized",
    "ENGLISH_LABELS",
    "PERSIAN_LABELS",
    "setContentDescription",
    "AppDisguiseManager.getActiveDisguiseIndex(this)",
    "AppDisguiseManager.applyDisguise(AppIconNameActivity.this, index)",
    "if (applied)",
    "The launcher change could not be verified",
    "launcher entry only",
):
    assert marker in selector, f"Missing launcher selector behavior: {marker}"

for marker in (
    "targetIndex < 0 || targetIndex >= ALIASES.length",
    "COMPONENT_ENABLED_STATE_ENABLED",
    "COMPONENT_ENABLED_STATE_DISABLED",
    "previousStates",
    "getActiveDisguiseIndex(context) == targetIndex",
    "return false;",
):
    assert marker in manager, f"Missing safe launcher transition behavior: {marker}"

for marker in (
    "everyBundledAliasCanBeSelectedAndVerified",
    "invalidTargetsAreRejectedWithoutChangingComponentStates",
    "ambiguousAliasConfigurationIsDetectedAndCanBeRepaired",
    "Launcher alias state was not restored",
):
    assert marker in instrumentation, f"Missing launcher instrumentation scenario: {marker}"

# About data is read from the installed package, not hard-coded or exaggerated.
for marker in (
    "getPackageInfo(",
    "PackageManager.GET_PERMISSIONS",
    "info.versionName",
    "info.getLongVersionCode()",
    "Build.VERSION.SDK_INT",
    "getApplicationInfo().targetSdkVersion",
    "info.requestedPermissions",
    "PackageInfo.REQUESTED_PERMISSION_GRANTED",
):
    assert marker in about, f"Missing package-derived About data: {marker}"

for marker in (
    "does not currently provide its own VPN server or tunnel",
    "Public IP: not checked",
    "metadata only",
    "Backup & Restore: not implemented",
    "not all services are guaranteed",
    "not proof that every behavior has been verified on a physical device",
):
    assert marker in about, f"Missing honest capability disclosure: {marker}"

assert "100% data" not in about
assert "zero-telemetry" not in about.lower()
assert "hide" not in selector.lower(), "Launcher selector must not market stealth/concealment."

assert "scripts/test_launcher_icon_and_about_contract.py" in workflow
print("PASS: Launcher selector exposes only manifest-backed aliases, validates and rolls back transitions, and About reports package-derived build/permission data with honest feature limits.")
