#!/usr/bin/env python3
"""Guard the read-only legacy environment metadata bridge and precedence wiring."""
from pathlib import Path

root = Path("app/src/main/java/com/veyravault/space")
clone_store = (root / "core/CloneStore.java").read_text(encoding="utf-8")
bridge = (root / "core/ProfileLegacyEnvironmentBridge.java").read_text(encoding="utf-8")
provider = (root / "core/ProfileRuntimeProvider.java").read_text(encoding="utf-8")
repository = (root / "core/AsyncCloneRepository.java").read_text(encoding="utf-8")
instrumentation = Path(
    "app/src/androidTest/java/com/veyravault/space/core/"
    "ProfileLegacyEnvironmentBridgeInstrumentationTest.java"
).read_text(encoding="utf-8")

assert "readGlobalEnvironmentMetadataProfileStrict" in clone_store
assert "values.containsKey(KEY_GLOBAL_DEV)" in clone_store
assert "readGlobalEnvStrict(c)" in clone_store
assert 'metadata.put("manufacturer"' in clone_store
assert 'metadata.put("deviceModel"' in clone_store
assert 'metadata.put("countryCode"' in clone_store
assert "simOperator" not in bridge
assert "CloneStore.readAllStrict(context)" in bridge
assert "entry.customDeviceEnabled" in bridge
assert "entry.packageName.equals(entry.packageName)" not in bridge
assert "packageName.equals(entry.packageName) && userId == entry.userId" in bridge
assert "!merged.contains(key) && !merged.isInvalid(key) && !merged.hasState(key)" in bridge
assert "return typed == null ? new ProfileDocument() : typed.copy();" in bridge
assert "ProfileLegacyEnvironmentBridge.mergeClone" in provider
assert "ProfileLegacyEnvironmentBridge.mergeGlobal" in provider
assert "ProfileLegacyEnvironmentBridge.mergeGlobal(appContext, merged)" in repository
assert "ProfileLegacyEnvironmentBridge.mergeClone(appContext, packageName, userId, merged)" in repository
assert "saveGlobalEnv" not in bridge
assert "saveAll" not in bridge
assert "ProfileDocumentStore.save" not in bridge
assert "same numeric Space/user ID, different package" in instrumentation
assert "ProfileRuntimeClient.resolveDocument" in instrumentation
assert "ProfileDocumentStore.clearCloneField" in instrumentation
assert "ProfileDocumentStore.clearGlobalField" in instrumentation
assert "absentOrDisabledGlobalLegacyProfileDoesNotImportConstructorDefaults" in instrumentation

print("Read-only legacy Global/Clone metadata bridge contract: PASS")
print("Typed override and explicit reset-state precedence contract: PASS")
print("Composite Clone identity and no-host-fallback contract: PASS")
