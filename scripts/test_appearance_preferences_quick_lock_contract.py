from pathlib import Path

root = Path("app/src/main")
appearance = (root / "java/com/veyravault/space/core/AppearanceManager.java").read_text(encoding="utf-8")
palette = (root / "java/com/veyravault/space/ui/UiPalette.java").read_text(encoding="utf-8")
base = (root / "java/com/veyravault/space/ui/BaseActivity.java").read_text(encoding="utf-8")
app = (root / "java/com/veyravault/space/VaultApp.java").read_text(encoding="utf-8")
settings = (root / "java/com/veyravault/space/ui/SettingsHubActivity.java").read_text(encoding="utf-8")
main = (root / "java/com/veyravault/space/ui/MainActivity.java").read_text(encoding="utf-8")
dashboard = (root / "java/com/veyravault/space/ui/DashboardActivity.java").read_text(encoding="utf-8")
security = (root / "java/com/veyravault/space/security/SecurityManager.java").read_text(encoding="utf-8")
lock_activity = (root / "java/com/veyravault/space/ui/SecurityLockActivity.java").read_text(encoding="utf-8")
styles = (root / "res/values/styles.xml").read_text(encoding="utf-8")
night_colors = (root / "res/values-night/colors.xml").read_text(encoding="utf-8")
card_drawable = (root / "res/drawable/bg_card_rounded.xml").read_text(encoding="utf-8")
workflow = Path(".github/workflows/build-and-audit.yml").read_text(encoding="utf-8")

# Persisted appearance is a separate preference domain; only known values are accepted.
for marker in (
    'private static final String PREFS = "veyra_appearance_prefs"',
    'private static final String KEY_THEME_MODE = "theme_mode"',
    'public static final String MODE_SYSTEM = "system"',
    'public static final String MODE_LIGHT = "light"',
    'public static final String MODE_DARK = "dark"',
    "AppCompatDelegate.MODE_NIGHT_FOLLOW_SYSTEM",
    "AppCompatDelegate.MODE_NIGHT_NO",
    "AppCompatDelegate.MODE_NIGHT_YES",
    ".putString(KEY_THEME_MODE, mode)",
    ".commit()",
):
    assert marker in appearance, f"Missing persisted appearance behavior: {marker}"

assert "AppearanceManager.apply(this);" in base
assert base.index("AppearanceManager.apply(this);") < base.index("super.onCreate(savedInstanceState)")
assert "AppearanceManager.apply(this);" in app
assert "AppearanceManager.getThemeMode(this)" in settings
assert "AppearanceManager.setThemeMode(SettingsHubActivity.this, mode)" in settings
for mode in ("MODE_SYSTEM", "MODE_LIGHT", "MODE_DARK"):
    assert f"AppearanceManager.{mode}" in settings

# DayNight resources and semantic palette must provide both themes.
assert "Theme.AppCompat.DayNight.NoActionBar" in styles
for name in ("bg_page", "bg_card", "bg_surface_secondary", "primary_blue", "primary_blue_light",
             "text_primary", "text_secondary"):
    assert f'name="{name}"' in night_colors, f"Missing night color resource: {name}"
assert '@color/bg_card' in card_drawable
for method in ("page(", "surface(", "textPrimary(", "textSecondary(", "muted(", "accent(",
               "accentSurface(", "success(", "warning(", "error("):
    assert method in palette, f"Missing semantic palette method: {method}"

# Quick Lock reuses the existing credential-verified lock state and current lock Activity.
assert "SecurityManager.isLockEnabled(this)" in base
assert "SecurityManager.lockSession();" in base
assert "new Intent(BaseActivity.this, SecurityLockActivity.class)" in base
assert "new Intent(BaseActivity.this, SecuritySettingsActivity.class)" in base
assert "if (!(this instanceof SecurityLockActivity) && !SecurityManager.isSessionUnlocked(this))" in base
assert "public static void lockSession()" in security
assert "SecurityManager.isSessionUnlocked(this)" in base
# The language control and lock switch share the top header on all primary screens.
for screen in (settings, main, dashboard):
    assert "createLanguageAction(fa)" in screen
    assert "createImmediateLockSwitch(fa)" in screen
assert "addLanguageSection(root, fa)" not in settings
assert "createLanguageAction(boolean fa)" in base
assert "createImmediateLockSwitch(boolean fa)" in base
assert 'setTextOn(fa ? "قفل" : "Locked")' in base
assert 'setTextOff(fa ? "باز" : "Open")' in base
assert "if (!isChecked)" in base
assert "SecurityManager.lockSession();" in base
assert "SecurityManager.verifyCredential" in lock_activity
assert "setImmediateLockSwitchChecked(SecurityManager.isLockEnabled(this)" in base
assert "new Intent(BaseActivity.this, SecurityLockActivity.class)" in base

instrumentation = Path("app/src/androidTest/java/com/veyravault/space/core/AppearanceManagerInstrumentationTest.java").read_text(encoding="utf-8")
for test_marker in (
    "missingPreferenceDefaultsToSystem",
    "lightAndDarkModesAreCommittedAndApplied",
    "systemModeIsPersistedAndApplied",
    "invalidModeIsRejectedWithoutOverwritingSavedPreference",
    "malformedPreferenceTypeFallsBackToSystem",
    "Appearance test preference restoration failed",
):
    assert test_marker in instrumentation, f"Missing appearance instrumentation scenario: {test_marker}"

# Existing About/Compatibility navigation remains available. No Clone/session data path is touched.
assert "AboutActivity.class" in settings
assert "repository." not in settings
assert "CloneStore." not in settings
assert "Engine." not in settings
assert "CloneStore." not in base
assert "Engine." not in base
assert "scripts/test_appearance_preferences_quick_lock_contract.py" in workflow

print("PASS: System/Light/Dark theme persistence, DayNight resources, shared language/header lock switch, authenticated quick-lock behavior, and no-unlock-bypass contract are present.")
