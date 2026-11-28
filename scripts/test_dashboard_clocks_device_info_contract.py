from pathlib import Path

source = Path("app/src/main/java/com/veyravault/space/ui/DashboardActivity.java").read_text(encoding="utf-8")

# Live clocks must use platform TextClock with explicit IANA zones, not hard-coded strings.
assert "new TextClock(this)" in source
assert 'clock.setTimeZone(zoneId)' in source
assert '"Asia/Tehran"' in source
assert '"America/New_York"' in source
assert 'clock.setFormat24Hour("hh:mm:ss a")' in source
assert 'clock.setFormat12Hour("hh:mm:ss a")' in source

# Device details are sourced from Android Build fields.
assert "Build.MANUFACTURER" in source
assert "Build.MODEL" in source
assert "Build.VERSION.RELEASE" in source

# Preserve asynchronous registry-backed counts and all existing dashboard destinations.
assert "AsyncCloneRepository.getInstance(getApplicationContext()).loadClones(" in source
assert "DashboardActivity.this,MainActivity.class" in source
assert "DashboardActivity.this,AddAppActivity.class" in source
assert "DashboardActivity.this,VpnStatusActivity.class" in source
assert "DashboardActivity.this,SettingsHubActivity.class" in source

print("PASS: Dashboard city clocks use live platform TextClock with Tehran/New York time zones.")
print("PASS: Device model/Android version are sourced from platform Build fields.")
print("PASS: Registry-backed counts and existing dashboard navigation remain present.")
