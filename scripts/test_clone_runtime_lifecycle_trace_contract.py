#!/usr/bin/env python3
"""Static safety contract for bounded Clone runtime lifecycle traces."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
trace = (root / "app/src/main/java/com/veyravault/space/core/CloneRuntimeTrace.java").read_text(encoding="utf-8")
engine = (root / "app/src/main/java/com/veyravault/space/core/Engine.java").read_text(encoding="utf-8")
callback = (root / "app/src/main/java/com/veyravault/space/core/CloneProfileLifecycleCallback.java").read_text(encoding="utf-8")
process_utils = (root / "app/src/main/java/com/veyravault/space/core/ProcessUtils.java").read_text(encoding="utf-8")
compatibility = (root / "app/src/main/java/com/veyravault/space/core/CompatibilityManager.java").read_text(encoding="utf-8")
doc = (root / "docs/STAGE_8_10_APP_COMPATIBILITY_DIAGNOSTICS.md").read_text(encoding="utf-8")
workflow = (root / ".github/workflows/build-and-audit.yml").read_text(encoding="utf-8")


def method_body(source, signature):
    start = source.index(signature)
    brace = source.index("{", start)
    depth = 0
    for index in range(brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[brace + 1:index]
    raise AssertionError("Unclosed method: " + signature)


for event in (
    "ENGINE_LAUNCH_REQUEST",
    "ENGINE_INSTALL_STATE_UNKNOWN",
    "ENGINE_INSTALL_FAILED",
    "ENGINE_HOOK_SYNC_BEGIN",
    "ENGINE_HOOK_SYNC_COMPLETE",
    "ENGINE_HOOK_SYNC_FAILED",
    "ENGINE_LAUNCH_CALL",
    "ENGINE_LAUNCH_ACCEPTED",
    "ENGINE_LAUNCH_REJECTED",
    "ENGINE_LAUNCH_EXCEPTION",
    "ENGINE_LIFECYCLE_CALLBACK_REGISTERED",
    "ENGINE_LIFECYCLE_CALLBACK_REGISTRATION_FAILED",
    "VIRTUAL_PROCESS_BEFORE_APP_CREATE",
    "TARGET_APPLICATION_ONCREATE_BEGIN",
    "TARGET_APPLICATION_ONCREATE_COMPLETE",
    "PROFILE_APPLY_RETURNED",
    "PROFILE_READBACK_VERIFIED",
    "PROFILE_READBACK_FAILED",
    "PROFILE_PROCESS_BOUNDARY_REJECTED",
):
    assert event in trace, event

assert 'TAG = "VeyraCloneRuntime"' in trace
assert "Log.i(TAG, line.toString())" in trace
assert "Math.min(value.length(), 96)" in trace
assert "c == '.' || c == '_' || c == ':' || c == '-'" in trace

# The trace utility must stay a pure Logcat sink: no durable or external storage.
for forbidden in (
    "SharedPreferences", "getSharedPreferences", "CloneStore", "FileOutputStream",
    "openFileOutput", "SQLiteDatabase", "HttpURLConnection", "OkHttpClient",
    "ContentResolver", "Log.getStackTraceString", "getMessage()",
):
    assert forbidden not in trace, forbidden

launch = method_body(engine, "public static CloneLaunchResult launchCloneDetailed(")
ordered = (
    "ENGINE_LAUNCH_REQUEST",
    "ENGINE_INSTALL_STATE_UNKNOWN",
    "ENGINE_HOOK_SYNC_BEGIN",
    "ENGINE_HOOK_SYNC_COMPLETE",
    "ENGINE_LAUNCH_CALL",
    "ENGINE_LAUNCH_ACCEPTED",
)
positions = [launch.index(item) for item in ordered]
assert positions == sorted(positions)
assert "failure.getMessage()" not in launch
assert "CloneRuntimeTrace.Event.ENGINE_LAUNCH_EXCEPTION" in launch

registration = method_body(
    engine, "public static boolean registerCloneProfileLifecycleCallback("
)
assert "ENGINE_LIFECYCLE_CALLBACK_REGISTERED" in registration
assert "ENGINE_LIFECYCLE_CALLBACK_REGISTRATION_FAILED" in registration
assert "recordLifecycleCallbackRegistration" in registration
assert "already_registered" in registration
assert "engine_unavailable" in registration
assert "registered" in registration
assert "ProcessUtils.currentProcessName(context)" in engine

before_create = method_body(
    callback, "public void beforeCreateApplication(String packageName, String processName,"
)
before_on_create = method_body(
    callback, "public void beforeApplicationOnCreate(String packageName, String processName,"
)
after_on_create = method_body(
    callback, "public void afterApplicationOnCreate(String packageName, String processName,"
)
assert "VIRTUAL_PROCESS_BEFORE_APP_CREATE" in before_create
assert "TARGET_APPLICATION_ONCREATE_BEGIN" in before_on_create
assert "TARGET_APPLICATION_ONCREATE_COMPLETE" in after_on_create
assert "CloneRuntimeTrace.Event.PROFILE_APPLY_RETURNED" in before_create
assert "CloneRuntimeTrace.Event.PROFILE_READBACK_VERIFIED" in before_create
assert "CloneRuntimeTrace.Event.PROFILE_READBACK_FAILED" in before_create
assert "PROFILE_PROCESS_BOUNDARY_REJECTED" in trace
assert "ProcessUtils.currentProcessName(appContext)" in before_create
assert "ProcessUtils.isBlackBoxWorkerProcess(hostProcessName, appContext.getPackageName())" in before_create
assert "public static boolean isBlackBoxWorkerProcess(String currentProcessName, String hostPackageName)" in process_utils
assert before_create.index("isBlackBoxWorkerProcess") < before_create.index("applySafeDefaults(packageContext)")
assert "target_context_mismatch" in before_create
assert '"readback_verified"' in before_create
assert '"readback_incomplete"' in before_create
assert "PROFILE_APPLIED" not in trace
assert "readback verified before Application creation" in callback
assert "readback did not verify" in callback
assert "error.getMessage()" not in callback
assert "blackBoxWorkerGateRejectsMainHostAndForeignProcesses" in (root / "app/src/androidTest/java/com/veyravault/space/core/ProfileRuntimeApplierInstrumentationTest.java").read_text(encoding="utf-8")

assert 'new CheckItem("runtime_trace"' in compatibility
assert "adb logcat -v threadtime -s VeyraCloneRuntime:I" in compatibility
assert "This snapshot does not read or share Logcat" in compatibility
assert "adb logcat -v threadtime -s VeyraCloneRuntime:I" in doc
assert "does not prove the first Activity was rendered" in doc
assert "not stored in CloneStore/SharedPreferences" in doc
assert "Test Clone runtime lifecycle trace contract" in workflow
assert "scripts/test_clone_runtime_lifecycle_trace_contract.py" in workflow

print("Clone runtime trace: allowlisted Engine and Application lifecycle milestones are wired: PASS")
print("Clone runtime trace: fields are sanitized and bounded before Logcat output: PASS")
print("Clone runtime trace: no file, preference, database, network or private-session access: PASS")
print("Clone runtime trace: CI contract and conservative interpretation are documented: PASS")
