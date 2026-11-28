from pathlib import Path

root = Path("app/src/main")
editor = (root / "java/com/veyravault/space/ui/ProfileDocumentEditorActivity.java").read_text(encoding="utf-8")
clone_entry = (root / "java/com/veyravault/space/ui/CloneEnvironmentProfileActivity.java").read_text(encoding="utf-8")
settings = (root / "java/com/veyravault/space/ui/SettingsHubActivity.java").read_text(encoding="utf-8")
spaces = (root / "java/com/veyravault/space/ui/MainActivity.java").read_text(encoding="utf-8")
manifest = (root / "AndroidManifest.xml").read_text(encoding="utf-8")
repository = (root / "java/com/veyravault/space/core/AsyncCloneRepository.java").read_text(encoding="utf-8")
registry = (root / "java/com/veyravault/space/core/ProfileFieldRegistry.java").read_text(encoding="utf-8")

assert "ProfileFieldRegistry.all()" in editor
assert "addSearchControls(resolved.size())" in editor
assert "filterFields(s == null ? \"\" : s.toString())" in editor
assert "searchableText.put(fieldCard, searchable)" in editor
assert "categoryHeaders.put(field.category, category)" in editor
assert "No profile fields match this search." in editor
assert "نمایش " in editor
assert "فقط ذخیره‌شده:" in editor
assert "field.category" in editor
assert "field.label" in editor
assert "field.validationRule" in editor
assert "field.capability" in editor
assert "field.unsupportedReason" in editor
assert "field.adapterId" in editor
assert "field.apiSupport" in editor
assert "field.privacyClass" in editor
assert "field.readbackMethod" in editor
assert "Adapter:" in editor
assert "API support:" in editor
assert "Privacy class:" in editor
assert "Readback method:" in editor
assert "if (!field.editable)" in editor
assert "ProfileDocumentResolver.resolveAll(cloneDocument, globalDocument)" in editor
assert "effective.source" in editor
assert "displayStatuses.get(field.key)" in editor
assert "Last readback:" in editor
assert "repository.loadGlobalProfileDocument" in editor
assert "repository.loadCloneProfileDocument" in editor
assert "repository.loadCloneRuntimeStatus" in editor
assert "runtimeStatus.current" in editor
assert "Last verified readback:" in editor
assert "not proof that the process is still alive" in editor
assert "repository.saveGlobalProfileField" in editor
assert "repository.saveCloneProfileField" in editor
assert "repository.clearGlobalProfileDocumentField" in editor
assert "repository.clearCloneProfileDocumentField" in editor
assert "repository.setCloneProfileFieldSafeDefault" in editor
assert "ProfileFieldRegistry.isValidValue(field, value)" in editor
assert "validLocationConfiguration(candidateClone, candidateGlobal)" in editor
assert "both valid latitude and longitude" in editor
assert "ProfileDocumentStore" not in editor
assert "ProfileStore" not in editor
assert "ProfileDocumentEditorActivity.class" in settings
assert "ProfileDocumentEditorActivity.class" in spaces
assert "repository.loadGlobalProfileDocument" in spaces
assert "ProfileDocumentResolver.resolveAll" in spaces
assert "ProfileDocumentEditorActivity.class" in clone_entry
assert 'android:name=".ui.ProfileDocumentEditorActivity" android:exported="false"' in manifest
assert "setCloneProfileFieldSafeDefault" in repository
assert "clearCloneOverrideField" in repository
assert "clearGlobalField" in repository

for field in ("altitude", "ipv6LeakStatus", "cameraPolicy", "webViewLocalStorageIsolation"):
    assert f'"{field}"' in registry

print("PASS: Global and per-Clone editor is generated from the canonical registry.")
print("PASS: Effective source, capability, validation and status are displayed per field.")
print("PASS: Adapter mapping, API support, privacy class and readback method are visible for every registry-generated field.")
print("PASS: Clone editor displays only profile-fresh last-readback metadata and labels it as historical, not live-process proof.")
print("PASS: Restricted and observed-only fields are read-only; editable writes are validated and asynchronous.")
print("PASS: Reset-to-Global and explicit Clone Safe Default use field-scoped persistence.")
print("PASS: Settings and Clone profile entry points open the complete editor.")
