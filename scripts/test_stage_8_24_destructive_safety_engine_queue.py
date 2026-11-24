from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "app/src/main/java/com/veyravault/space/ui"
CORE = ROOT / "app/src/main/java/com/veyravault/space/core"

main = (UI / "MainActivity.java").read_text(encoding="utf-8")
engine = (CORE / "Engine.java").read_text(encoding="utf-8")
per_clone = (UI / "AppCompatibilityDiagnosticsActivity.java").read_text(encoding="utf-8")
compat_report = (UI / "CompatibilityReportActivity.java").read_text(encoding="utf-8")
dashboard = (UI / "DashboardActivity.java").read_text(encoding="utf-8")
queue = (CORE / "EngineOperationQueue.java").read_text(encoding="utf-8")

# Destructive per-Clone actions require an explicit warning and affirmative action.
assert "confirmClearCloneData(item)" in main
assert "confirmUninstallClone(item)" in main
assert "confirmBatchUninstall(all, checked, selected)" in main
for evidence in (
    "This action cannot be undone",
    "Saved sign-ins and sessions",
    "make an independent backup",
    "Final confirmation for batch uninstall",
    "may be permanently lost",
):
    assert evidence in main, f"Missing destructive-action warning: {evidence}"
assert main.index("confirmClearCloneData(item)") < main.index("Engine.clearCloneData(item.packageName")
assert main.index("confirmUninstallClone(item)") < main.index("Engine.uninstallClone(item.packageName")
assert main.index("confirmBatchUninstall(all, checked, selected)") < main.index("runBatchUninstall(all, checked, 0")

# Engine wrappers report dispatch only; they do not fabricate successful completion.
assert "public static boolean stopClone(String pkg, int userId)" in engine
assert "public static boolean clearCloneData(String pkg, int userId)" in engine
assert "pinned Engine clearPackage call returns normally" in engine
assert "may still mean partial deletion occurred" in engine
assert "forensic secure-erasure guarantee" in engine
assert "process-termination result" in engine
assert "Engine.clearCloneData(item.packageName, item.userId),\n                            (dispatched, failure)" in main
assert "Boolean.TRUE.equals(dispatched)" in main
assert "Engine.stopClone(item.packageName, item.userId)" in main

# All production Activity callers of CompatibilityManager perform Engine work through
# the single process-wide Engine queue, rather than private Executors or the UI thread.
assert "EngineOperationQueue.submit" in per_clone
assert "CompatibilityManager.formatCloneReport(getApplicationContext(), clone)" in per_clone
assert "ExecutorService diagnosticsWorker" not in per_clone
assert "EngineOperationQueue.submit" in compat_report
assert "CompatibilityManager.collect(getApplicationContext())" in compat_report
assert "CompatibilityManager.collect(this)" not in compat_report
assert "EngineOperationQueue.submit" in dashboard
assert "Engine.getCore()" in dashboard
assert "dashboardStatusExecutor" not in dashboard
assert "ExecutorService" not in dashboard
assert "private static final ExecutorService ENGINE" in queue

print("PASS: Clear Data and single/batch uninstall require explicit, data-loss-aware confirmation.")
print("PASS: Stop and Clear wrappers distinguish dispatch from verified completion.")
print("PASS: compatibility and Dashboard Engine diagnostics share the serialized Engine queue.")
