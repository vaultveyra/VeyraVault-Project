#!/usr/bin/env python3
"""Synthetic checks for Android ELF ABI/API metadata and Gradle NDK platform alignment."""
from pathlib import Path
import struct
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from audit_native_elf import NativeElfError, inspect_android_elf, validate_native_libraries
import prepare_workspace


def make_android_elf(elf_class, machine, api_level):
    endian = "<"
    ident = b"\x7fELF" + bytes((elf_class, 1, 1)) + b"\0" * 9
    owner = b"Android\0"
    descriptor = (
        struct.pack(endian + "I", api_level)
        + b"r27\0".ljust(64, b"\0")
        + b"12077973\0".ljust(64, b"\0")
    )
    note = (
        struct.pack(endian + "III", len(owner), len(descriptor), 1)
        + owner + b"\0" * ((-len(owner)) % 4)
        + descriptor + b"\0" * ((-len(descriptor)) % 4)
    )
    names = b"\0.note.android.ident\0.shstrtab\0"
    if elf_class == 1:
        header_size, section_size = 52, 40
        note_offset = header_size
        names_offset = (note_offset + len(note) + 3) & ~3
        section_offset = names_offset + len(names)
        null = b"\0" * section_size
        note_section = struct.pack(endian + "IIIIIIIIII", 1, 7, 0, 0,
                                   note_offset, len(note), 0, 0, 4, 0)
        names_section = struct.pack(endian + "IIIIIIIIII", names.index(b".shstrtab"), 3, 0, 0,
                                    names_offset, len(names), 0, 0, 1, 0)
        header = struct.pack(endian + "HHIIIIIHHHHHH", 3, machine, 1, 0, 0,
                             section_offset, 0, header_size, 0, 0, section_size, 3, 2)
    elif elf_class == 2:
        header_size, section_size = 64, 64
        note_offset = header_size
        names_offset = (note_offset + len(note) + 3) & ~3
        section_offset = names_offset + len(names)
        null = b"\0" * section_size
        note_section = struct.pack(endian + "IIQQQQIIQQ", 1, 7, 0, 0,
                                   note_offset, len(note), 0, 0, 4, 0)
        names_section = struct.pack(endian + "IIQQQQIIQQ", names.index(b".shstrtab"), 3, 0, 0,
                                    names_offset, len(names), 0, 0, 1, 0)
        header = struct.pack(endian + "HHIQQQIHHHHHH", 3, machine, 1, 0, 0,
                             section_offset, 0, header_size, 0, 0, section_size, 3, 2)
    else:
        raise ValueError("ELF class must be 1 or 2")
    return ident + header + note + b"\0" * (names_offset - (note_offset + len(note))) + names + null + note_section + names_section


class FakeArchive:
    def __init__(self, entries):
        pairs = list(entries)
        self.entries = [name for name, _ in pairs]
        self.contents = dict(pairs)

    def namelist(self):
        return list(self.entries)

    def read(self, name):
        return self.contents[name]


for elf_class, machine in ((1, 40), (2, 183)):
    metadata = inspect_android_elf(make_android_elf(elf_class, machine, 21))
    assert metadata["elf_class"] == elf_class
    assert metadata["machine"] == machine
    assert metadata["android_api"] == 21
    assert metadata["ndk_version"] == "r27"
    assert metadata["ndk_build"] == "12077973"

valid = FakeArchive([
    ("lib/armeabi-v7a/libblackbox.so", make_android_elf(1, 40, 21)),
    ("lib/arm64-v8a/libblackbox.so", make_android_elf(2, 183, 21)),
])
assert len(validate_native_libraries(valid, 21)) == 2


def expect_rejection(archive, reason):
    try:
        validate_native_libraries(archive, 21)
    except NativeElfError:
        return
    raise AssertionError("Native ELF policy accepted invalid fixture: " + reason)


expect_rejection(FakeArchive([
    ("lib/armeabi-v7a/libblackbox.so", make_android_elf(1, 40, 24)),
    ("lib/arm64-v8a/libblackbox.so", make_android_elf(2, 183, 21)),
]), "native API above app minSdk")
expect_rejection(FakeArchive([
    ("lib/armeabi-v7a/libblackbox.so", make_android_elf(2, 183, 21)),
    ("lib/arm64-v8a/libblackbox.so", make_android_elf(2, 183, 21)),
]), "wrong ELF class or machine")
expect_rejection(FakeArchive([
    ("lib/armeabi-v7a/libblackbox.so", b"not an ELF"),
    ("lib/arm64-v8a/libblackbox.so", make_android_elf(2, 183, 21)),
]), "malformed ELF")
expect_rejection(FakeArchive([
    ("lib/armeabi-v7a/libblackbox.so", make_android_elf(1, 40, 21)),
]), "missing ARM64 Engine library")
expect_rejection(FakeArchive([
    ("lib/armeabi-v7a/libblackbox.so", make_android_elf(1, 40, 21)),
    ("lib/arm64-v8a/libblackbox.so", make_android_elf(2, 183, 21)),
    ("lib/x86/libextra.so", make_android_elf(1, 3, 21)),
]), "unsupported ABI")

with tempfile.TemporaryDirectory() as directory:
    workspace = Path(directory)
    application_mk = workspace / "Bcore/src/main/cpp/Application.mk"
    application_mk.parent.mkdir(parents=True)
    application_mk.write_text(
        "APP_ABI := armeabi-v7a arm64-v8a\n"
        "APP_PLATFORM := android-24\n"
        "APP_STL := c++_static\n", encoding="utf-8"
    )
    prepare_workspace.align_native_application_platform(str(workspace), 21)
    updated = application_mk.read_text(encoding="utf-8")
    assert "APP_ABI := armeabi-v7a arm64-v8a" in updated
    assert "APP_STL := c++_static" in updated
    assert "APP_PLATFORM" not in updated

audit_source = (ROOT / "scripts/audit_apk.py").read_text(encoding="utf-8")
prepare_source = (ROOT / "scripts/prepare_workspace.py").read_text(encoding="utf-8")
workflow = (ROOT / ".github/workflows/build-and-audit.yml").read_text(encoding="utf-8")
doc = ROOT / "docs/STAGE_8_31_NATIVE_ELF_COMPATIBILITY.md"
assert "align_native_application_platform(WORKSPACE, int(min_sdk))" in prepare_source
assert "detect_workspace_min_sdk(WORKSPACE)" in prepare_source
assert "--min-api" in prepare_source
assert "validate_native_libraries" in audit_source
assert "NativeElfError" in audit_source
assert "Test Stage 8.31 Native ELF compatibility" in workflow
assert "test_stage_8_31_native_elf_compatibility.py" in workflow
assert doc.is_file()

print("PASS: ELF32/ARM and ELF64/AArch64 Android identification notes decode correctly.")
print("PASS: API 21 libraries pass for minSdk 21; API 24 and malformed/mismatched ELF fail.")
print("PASS: Missing Engine ABI and unapproved native ABI are rejected.")
print("PASS: Only ephemeral workspace loses the stale APP_PLATFORM override.")
print("PASS: CI audits each native ELF against the agreed effective minSdk.")
