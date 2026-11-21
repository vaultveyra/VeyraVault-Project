from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = (root / "app/src/main/java/com/veyravault/space/ui/DashboardActivity.java").read_text(encoding="utf-8")
security_source = (root / "app/src/main/java/com/veyravault/space/security/SecurityManager.java").read_text(encoding="utf-8")

# The summary is refreshed with Activity lifecycle awareness.
assert "private static volatile boolean sessionUnlocked = false;" in security_source
assert "refreshReadOnlyPlatformStatus();" in source
assert "dashboardStatusExecutor = Executors.newSingleThreadExecutor()" in source
assert "dashboardStatusExecutor.shutdownNow()" in source
assert "generation != dashboardStatusGeneration" in source
assert "dateRefreshHandler.post(() ->" in source

# Read-only sources: no credential verification, lock mutation, or Device Admin mutation.
start = source.index("private void refreshReadOnlyPlatformStatus()")
end = source.index("private String describeProfileLifecycle(", start)
loader = source[start:end]
for marker in (
    "SecurityManager",
    ".isLockEnabled(appContext)",
    ".isSessionUnlocked(appContext)",
    "VaultDeviceAdminReceiver.isAntiUninstallActive(appContext)",
    "Engine.getCore()",
    "Engine.getProfileLifecycleDiagnostic()",
):
    assert marker in loader, f"Missing read-only status source: {marker}"

for forbidden in (
    "setLockCredential(",
    "verifyCredential(",
    "lockSession(",
    "setAntiUninstallEnabled(",
    "removeActiveAdmin(",
    "clearCloneData(",
    "uninstallClone(",
):
    assert forbidden not in loader, f"Dashboard status loader must not mutate state: {forbidden}"

# Engine presence must not be presented as full readiness.
assert "Core detected; full readiness is not verified" in source
assert "Core detected" in source
assert "Core detected; full readiness is not verified" in loader
assert "Engine ready" not in loader

# Lifecycle diagnostic is mapped to bounded, known labels; raw diagnostic text is not rendered.
formatter_start = source.index("private String describeProfileLifecycle(")
formatter_end = source.index("private String describeHostNetwork(", formatter_start)
formatter = source[formatter_start:formatter_end]
for marker in (
    '"REGISTERED"',
    '"NOT_REGISTERED"',
    '"ENGINE_UNAVAILABLE"',
    '"INVALID_CONTEXT"',
    '"REGISTRATION_FAILED:"',
    '"Unknown status"',
):
    assert marker in formatter, f"Missing safe lifecycle mapping: {marker}"
assert "setText(diagnostic)" not in source

# Both languages and explicit read-only disclosure are present.
for marker in (
    "Security & Engine Status (Read-only)",
    "وضعیت امنیت و موتور (فقط خواندنی)",
    "This panel is read-only and does not change security settings.",
    "این بخش فقط وضعیت را می‌خواند و هیچ تنظیم امنیتی را تغییر نمی‌دهد.",
    "Android Device Admin:",
    "Clone profile lifecycle:",
):
    assert marker in source, f"Missing localized status text: {marker}"

print("PASS: Dashboard reads app-lock, Device Admin and Engine diagnostics without changing them.")
print("PASS: Engine core detection is not overstated as full readiness.")
print("PASS: Lifecycle diagnostics are mapped to bounded labels.")
print("PASS: Background refresh is lifecycle-aware and returns UI updates to the main thread.")
