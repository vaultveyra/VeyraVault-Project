from pathlib import Path

source = Path("app/src/main/java/com/veyravault/space/ui/MainActivity.java").read_text(encoding="utf-8")

# Compact five-destination bottom navigation keeps all existing destinations wired.
for label in ("DashboardActivity.class", "refreshSpaces();", "AddAppActivity.class",
              "VpnStatusActivity.class", "SettingsHubActivity.class"):
    assert label in source, f"Missing existing navigation destination: {label}"

# Navigation items are icon + label controls with accessible descriptions.
assert "private View makeNavButton(String title, int iconRes, boolean active" in source
assert "icon.setImageResource(iconRes)" in source
assert "item.setContentDescription(title)" in source
assert "android.R.drawable.ic_menu_view" in source
assert "android.R.drawable.ic_menu_agenda" in source
assert "android.R.drawable.ic_menu_compass" in source
assert "android.R.drawable.ic_menu_preferences" in source

# The central Add action is an icon and density-independent compact touch target.
assert "ImageView fabPlus = new ImageView(this)" in source
assert "android.R.drawable.ic_input_add" in source
assert "new LinearLayout.LayoutParams(dp(48), dp(48))" in source
assert "new LinearLayout.LayoutParams(132, 132)" not in source
assert "private int dp(int value)" in source

print("PASS: Spaces bottom navigation retains all five destinations with icon-led accessible items.")
print("PASS: Add-app action uses a compact 48dp icon target instead of the previous oversized 132px text control.")
