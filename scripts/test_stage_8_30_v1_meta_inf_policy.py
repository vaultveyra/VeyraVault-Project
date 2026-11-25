#!/usr/bin/env python3
"""Stage 8.30 tests for the exact META-INF allowlist and V1 warning policy."""
from pathlib import Path

from audit_apk import (
    EXPECTED_META_INF_ENTRIES,
    REQUIRED_SERVICE_PROVIDERS,
    validate_meta_inf_entries,
)

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github/workflows/build-and-audit.yml").read_text(encoding="utf-8")
doc = ROOT / "docs/STAGE_8_30_V1_META_INF_POLICY.md"


class FakeArchive:
    def __init__(self, entries):
        self.entries = list(entries)
        self.contents = dict(entries)

    def namelist(self):
        return list(self.entries)

    def read(self, name):
        return self.contents[name]


valid_entries = {
    "META-INF/com/android/build/gradle/app-metadata.properties":
        b"androidGradlePluginVersion=8.13.2\n",
}
for resource_name, provider_name in REQUIRED_SERVICE_PROVIDERS.items():
    valid_entries[resource_name] = (provider_name + "\n").encode("utf-8")

assert set(REQUIRED_SERVICE_PROVIDERS).issubset(EXPECTED_META_INF_ENTRIES)
assert set(validate_meta_inf_entries(FakeArchive(valid_entries.items()))) == set(valid_entries)

# The AGP metadata file is optional, while both production ServiceLoader files are required.
without_agp_metadata = {
    name: value for name, value in valid_entries.items()
    if name != "META-INF/com/android/build/gradle/app-metadata.properties"
}
assert set(validate_meta_inf_entries(FakeArchive(without_agp_metadata.items()))) == set(without_agp_metadata)


def expect_rejection(entries, reason):
    try:
        validate_meta_inf_entries(FakeArchive(entries))
    except ValueError:
        return
    raise AssertionError("META-INF policy accepted invalid fixture: " + reason)


unknown_entry = dict(valid_entries)
unknown_entry["META-INF/unknown.payload"] = b"unexpected"
expect_rejection(unknown_entry.items(), "unknown META-INF payload")

wrong_provider = dict(valid_entries)
wrong_provider["META-INF/services/kotlinx.coroutines.internal.MainDispatcherFactory"] = b"attacker.Provider\n"
expect_rejection(wrong_provider.items(), "unexpected ServiceLoader provider")

missing_service = {
    name: value for name, value in valid_entries.items()
    if name != "META-INF/services/kotlinx.coroutines.CoroutineExceptionHandler"
}
expect_rejection(missing_service.items(), "missing required service descriptor")

duplicate_entries = list(valid_entries.items())
duplicate_entries.append(duplicate_entries[0])
expect_rejection(duplicate_entries, "duplicate META-INF path")

# The isolated signer job permits only the exact known V1 META-INF warnings.
assert "UNPROTECTED_WARNINGS=" in workflow
for path in (
    "META-INF/com/android/build/gradle/app-metadata.properties",
    "META-INF/services/kotlinx.coroutines.CoroutineExceptionHandler",
    "META-INF/services/kotlinx.coroutines.internal.MainDispatcherFactory",
):
    assert path in workflow, f"Signer policy missing allow-listed warning: {path}"
assert "not protected by signature" in workflow
assert "UNPROTECTED_WARNINGS=" in workflow
for signature in (
    "Verified using v1 scheme (JAR signing): true",
    "Verified using v2 scheme (APK Signature Scheme v2): true",
    "Verified using v3 scheme (APK Signature Scheme v3): true",
):
    assert signature in workflow
assert 'grep -Fq "not protected by signature" <<< "$VERIFY_OUTPUT"' not in workflow
assert doc.is_file()

print("PASS: Exact META-INF allowlist accepts only known AGP provenance and required coroutine descriptors.")
print("PASS: Unknown entries, missing descriptors, duplicate paths and provider drift are rejected.")
print("PASS: Signer allows only the three known V1 META-INF warnings and still requires V1/V2/V3 verification.")
