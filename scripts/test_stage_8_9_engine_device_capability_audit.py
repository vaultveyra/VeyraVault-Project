from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
workspace = (ROOT / "scripts/prepare_workspace.py").read_text(encoding="utf-8")
settings = (ROOT / "app/src/main/java/com/veyravault/space/core/ProfileSettings.java").read_text(encoding="utf-8")
provider = (ROOT / "app/src/main/java/com/veyravault/space/core/ProfileRuntimeProvider.java").read_text(encoding="utf-8")
client = (ROOT / "app/src/main/java/com/veyravault/space/core/ProfileRuntimeClient.java").read_text(encoding="utf-8")
lifecycle = (ROOT / "app/src/main/java/com/veyravault/space/core/CloneProfileLifecycleCallback.java").read_text(encoding="utf-8")
runtime_applier = (ROOT / "app/src/main/java/com/veyravault/space/core/ProfileRuntimeApplier.java").read_text(encoding="utf-8")
runtime_trace = (ROOT / "app/src/main/java/com/veyravault/space/core/CloneRuntimeTrace.java").read_text(encoding="utf-8")
runtime_tests = (ROOT / "app/src/androidTest/java/com/veyravault/space/core/ProfileRuntimeApplierInstrumentationTest.java").read_text(encoding="utf-8")
process_utils = (ROOT / "app/src/main/java/com/veyravault/space/core/ProcessUtils.java").read_text(encoding="utf-8")
virtual_hooks = (ROOT / "app/src/main/java/com/veyravault/space/core/VirtualHookManager.java").read_text(encoding="utf-8")
audit = (ROOT / "docs/STAGE_8_9_ENGINE_DEVICE_CAPABILITY_AUDIT.md").read_text(encoding="utf-8")
workflow = (ROOT / ".github/workflows/build-and-audit.yml").read_text(encoding="utf-8")

PINNED_ENGINE_COMMIT = "89b59836c66f173756a4ae258cf379a957649820"
match = re.search(r'ENGINE_COMMIT\s*=\s*"([0-9a-f]{40})"', workspace)
assert match and match.group(1) == PINNED_ENGINE_COMMIT, "The audited Engine revision must match the build pin."

profile_fields = (
    "localeTag",
    "timeZoneId",
    "locationEnabled",
    "latitude",
    "longitude",
)
for field in profile_fields:
    assert re.search(r"\b" + re.escape(field) + r"\b", settings), f"ProfileSettings is missing {field}"
    assert f'"{field}"' in provider, f"ProfileRuntimeProvider does not encode {field}"
    assert f'"{field}"' in client, f"ProfileRuntimeClient does not decode {field}"

assert "Binder.getCallingUid() != Process.myUid()" in provider, (
    "Profile runtime IPC must remain restricted to the app UID."
)
assert "ProfileStore.readCloneOverrideStrict(context, packageName, userId)" in provider
assert "ProfileStore.readGlobalStrict(context)" in provider
assert "beforeCreateApplication" in lifecycle
assert "ProfileRuntimeClient.resolve(appContext, packageName, userId)" in lifecycle
assert "ProfileRuntimeApplier.applyAndVerify(packageContext, packageName, resolved)" in lifecycle
assert "verification.isFullyVerified()" in lifecycle
assert "PROFILE_READBACK_VERIFIED" in lifecycle
assert "PROFILE_READBACK_FAILED" in lifecycle
assert "expectedPackageName.equals(actualPackageName)" in runtime_applier
assert "Locale.getDefault()" in runtime_applier
assert "readResourceLocaleTag(packageContext)" in runtime_applier
assert "TimeZone.getDefault()" in runtime_applier
assert "ApplyStatus.APPLIED" in runtime_applier
assert "PROFILE_READBACK_VERIFIED" in runtime_trace
assert "PROFILE_READBACK_FAILED" in runtime_trace
assert "PROFILE_PROCESS_BOUNDARY_REJECTED" in runtime_trace
assert "ProcessUtils.currentProcessName(appContext)" in lifecycle
assert "ProcessUtils.isBlackBoxWorkerProcess(hostProcessName, appContext.getPackageName())" in lifecycle
assert "public static boolean isBlackBoxWorkerProcess(String currentProcessName, String hostPackageName)" in process_utils
assert lifecycle.index("isBlackBoxWorkerProcess") < lifecycle.index("applySafeDefaults(packageContext)")
assert "blackBoxWorkerGateRejectsMainHostAndForeignProcesses" in runtime_tests

for marker in (
    '"setPattern"',
    '"setLocation"',
    '"getPattern"',
    '"getLocation"',
    "userId, packageName, location",
    "OWN_MODE_AND_COORDINATES_READ_BACK",
):
    assert marker in virtual_hooks, f"Missing package/user-scoped location behavior: {marker}"

for unsupported_field in (
    "imei",
    "meid",
    "imsi",
    "serialNumber",
    "androidId",
    "wifiMac",
    "bssid",
    "deviceModel",
    "manufacturer",
    "buildFingerprint",
):
    assert unsupported_field.lower() not in settings.lower(), (
        f"Unsupported device identity must not silently enter ProfileSettings: {unsupported_field}"
    )

for evidence in (
    PINNED_ENGINE_COMMIT,
    "BDeviceManager",
    "BDeviceConfig",
    "ITelephonyManagerProxy",
    "IDeviceIdentifiersPolicyProxy",
    "IWifiManagerProxy",
    "AndroidIdProxy",
    "MD5(BlackBoxCore.getHostPkg())",
    "BlackBox_Wifi",
    "getAllCellInfo",
    "getCellLocation",
    "getNeighboringCellInfo",
    "SparseArray<HashMap<String, BLocationConfig>>",
    "package/user-scoped",
):
    assert evidence in audit, f"Stage 8.9 audit is missing a required source finding: {evidence}"

assert "test_stage_8_9_engine_device_capability_audit.py" in workflow, (
    "CI must run the Stage 8.9 Engine capability audit contract."
)

print("PASS: The Engine source audit is tied to the exact immutable build pin.")
print("PASS: The current runtime profile transports only Locale, Time Zone, and package/user-scoped Location fields.")
print("PASS: Profile runtime IPC remains same-UID and resolves strict per-Clone/global settings.")
print("PASS: Location hooks use package/user-scoped Engine calls with pattern/coordinate readback.")
print("PASS: Device identifiers and unsupported Build/Wi-Fi fields are not silently represented as configurable ProfileSettings.")
print("PASS: The audit documents active Engine proxies separately from genuine per-Clone profile APIs.")
print("PASS: CI is wired to prevent the capability audit from silently disappearing.")
