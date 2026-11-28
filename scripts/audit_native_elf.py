#!/usr/bin/env python3
"""Fail-closed Android ELF ABI and minimum-API validation for packaged native libraries."""
import struct
from collections import Counter

ABI_LAYOUTS = {
    "armeabi-v7a": (1, 40, "ELF32/ARM"),
    "arm64-v8a": (2, 183, "ELF64/AArch64"),
}
REQUIRED_ENGINE_LIBRARIES = {
    "lib/armeabi-v7a/libblackbox.so",
    "lib/arm64-v8a/libblackbox.so",
}


class NativeElfError(ValueError):
    pass


def inspect_android_elf(data):
    if not isinstance(data, (bytes, bytearray)) or len(data) < 64 or data[:4] != b"\x7fELF":
        raise NativeElfError("Native library is not a complete ELF file")
    cls, encoding = data[4], data[5]
    endian = "<" if encoding == 1 else ">" if encoding == 2 else None
    if cls not in (1, 2) or endian is None:
        raise NativeElfError("Unsupported ELF class or byte order")
    machine = struct.unpack_from(endian + "H", data, 18)[0]
    if cls == 1:
        shoff = struct.unpack_from(endian + "I", data, 32)[0]
        entsize, count, names_index = struct.unpack_from(endian + "HHH", data, 46)
        fmt = endian + "IIIIIIIIII"
    else:
        shoff = struct.unpack_from(endian + "Q", data, 40)[0]
        entsize, count, names_index = struct.unpack_from(endian + "HHH", data, 58)
        fmt = endian + "IIQQQQIIQQ"
    size = struct.calcsize(fmt)
    if not shoff or not count or names_index >= count or entsize < size:
        raise NativeElfError("ELF section table is invalid")
    if shoff + entsize * count > len(data):
        raise NativeElfError("ELF section table is truncated")
    sections = [
        struct.unpack_from(fmt, data, shoff + i * entsize) for i in range(count)
    ]
    names_header = sections[names_index]
    names_off, names_len = names_header[4], names_header[5]
    if names_off + names_len > len(data):
        raise NativeElfError("ELF section-name table is truncated")
    names = data[names_off:names_off + names_len]
    android_notes = []
    for section in sections:
        name_off, section_type = section[0], section[1]
        if name_off >= len(names):
            continue
        end = names.find(b"\0", name_off)
        if end < 0 or names[name_off:end] != b".note.android.ident" or section_type != 7:
            continue
        offset, length = section[4], section[5]
        limit = offset + length
        if limit > len(data):
            raise NativeElfError("Android ELF note section is truncated")
        pos = offset
        while pos + 12 <= limit:
            namesz, descsz, note_type = struct.unpack_from(endian + "III", data, pos)
            pos += 12
            owner_end = pos + namesz
            if owner_end > limit:
                raise NativeElfError("Android ELF note owner is truncated")
            owner = data[pos:owner_end]
            pos = (owner_end + 3) & ~3
            desc_end = pos + descsz
            if desc_end > limit:
                raise NativeElfError("Android ELF note descriptor is truncated")
            desc = data[pos:desc_end]
            pos = (desc_end + 3) & ~3
            if owner.rstrip(b"\0") == b"Android" and note_type == 1:
                if len(desc) < 132:
                    raise NativeElfError("Android ELF identification note is too small")
                api = struct.unpack_from(endian + "I", desc, 0)[0]
                ndk = desc[4:68].split(b"\0", 1)[0].decode("ascii", "replace")
                build = desc[68:132].split(b"\0", 1)[0].decode("ascii", "replace")
                android_notes.append((api, ndk, build))
    if not android_notes or len(set(android_notes)) != 1:
        raise NativeElfError("Missing or conflicting .note.android.ident metadata")
    api, ndk, build = android_notes[0]
    if api < 1:
        raise NativeElfError("Android ELF API level is invalid")
    return {"elf_class": cls, "machine": machine, "android_api": api,
            "ndk_version": ndk, "ndk_build": build}


def validate_native_libraries(archive, min_api):
    if not isinstance(min_api, int) or min_api < 1:
        raise NativeElfError("Application minSdk must be a positive integer")
    paths = sorted(
        n for n in archive.namelist()
        if n.startswith("lib/") and n.endswith(".so")
    )
    if not paths:
        raise NativeElfError("No native shared libraries were found")
    duplicates = sorted(n for n, count in Counter(paths).items() if count > 1)
    if duplicates:
        raise NativeElfError("Duplicate native library paths: " + ", ".join(duplicates))
    missing = sorted(REQUIRED_ENGINE_LIBRARIES - set(paths))
    if missing:
        raise NativeElfError("Required Engine ABI libraries are missing: " + ", ".join(missing))

    results = []
    for path in paths:
        parts = path.split("/")
        if len(parts) != 3 or parts[0] != "lib" or parts[1] not in ABI_LAYOUTS:
            raise NativeElfError("Malformed or unsupported native ABI path: " + path)
        expected_class, expected_machine, label = ABI_LAYOUTS[parts[1]]
        try:
            meta = inspect_android_elf(archive.read(path))
        except Exception as exc:
            raise NativeElfError("{}: {}".format(path, exc)) from exc
        if meta["elf_class"] != expected_class or meta["machine"] != expected_machine:
            raise NativeElfError(
                "{} has ELF class {} / machine {}, expected {}".format(
                    path, meta["elf_class"], meta["machine"], label
                )
            )
        if meta["android_api"] > min_api:
            raise NativeElfError(
                "{} targets Android API {}, above app minSdk {}".format(
                    path, meta["android_api"], min_api
                )
            )
        results.append((path, label, meta))
    return results
