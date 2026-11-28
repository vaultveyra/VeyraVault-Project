from pathlib import Path

source = Path("app/src/main/java/com/veyravault/space/ui/DashboardActivity.java").read_text(encoding="utf-8")

# Dashboard and Spaces must expose the same persistent five-destination navigation shell.
for marker in (
    "createBottomNavigation(fa, scroll)",
    'fa ? "داشبورد" : "Dashboard"',
    'fa ? "فضاها" : "Spaces"',
    'fa ? "تنظیمات" : "Settings"',
    'android.R.drawable.ic_menu_compass',
    "new Intent(DashboardActivity.this, MainActivity.class)",
    "new Intent(DashboardActivity.this, AddAppActivity.class)",
    "new Intent(DashboardActivity.this, VpnStatusActivity.class)",
    "new Intent(DashboardActivity.this, SettingsHubActivity.class)",
    "setContentView(shell)",
):
    assert marker in source, f"Missing Dashboard navigation behavior: {marker}"

# The center Add action remains a real, accessible touch target.
assert "add.setContentDescription(fa ? \"افزودن برنامه\" : \"Add app\")" in source
assert "add.setClickable(true)" in source
assert "add.setFocusable(true)" in source
assert "add.setOnClickListener" in source
assert "addParams = new LinearLayout.LayoutParams(dp(48), dp(48))" in source

# Preserve existing Dashboard data loading and top-bar security/language controls.
assert "createLanguageAction(fa)" in source
assert "createImmediateLockSwitch(fa)" in source
assert "AsyncCloneRepository.getInstance(getApplicationContext()).loadClones(" in source
assert "loadEffectiveProfileSummary(result.getValue(), profileSummary, fa)" in source

print("PASS: Dashboard exposes Dashboard, Spaces, Add, VPN and Settings destinations.")
print("PASS: Center Add action is accessible and opens AddAppActivity.")
print("PASS: Existing language/lock controls and asynchronous Dashboard data remain intact.")
