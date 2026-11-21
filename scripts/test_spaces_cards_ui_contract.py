from pathlib import Path

source = Path("app/src/main/java/com/veyravault/space/ui/MainActivity.java").read_text(encoding="utf-8")

# Space cards retain collapse/expand persistence and GMS controls.
assert "repository.setSpaceCollapsed(spaceNum, !collapsed" in source
assert "Engine.isGmsInstalled(uid)" in source
assert "Engine.setGmsEnabled(uid, next)" in source
assert "private View buildSpaceCard(" in source

# Clone cells retain the existing async launch and per-clone configuration actions.
assert "launchRepository.launchClone(item.packageName, item.userId" in source
assert "showCloneConfigBottomSheet(item)" in source
assert "private View buildCloneCell(" in source

# Responsive, density-independent card and clone-grid dimensions.
assert "card.setPadding(dp(18), dp(16), dp(18), dp(16))" in source
assert "card.setElevation(dp(2))" in source
assert "grid.setColumnCount(3)" in source
assert "getDisplayMetrics().widthPixels - dp(64)) / 3" in source
assert "new FrameLayout.LayoutParams(dp(64), dp(64), Gravity.CENTER)" in source
assert "new LinearLayout.LayoutParams(dp(28), dp(28))" in source

print("PASS: Spaces collapse/GMS actions and async clone launch/configuration paths remain present.")
print("PASS: Space cards and clone grid use compact density-independent dimensions.")
