#!/usr/bin/env python3
import argparse
import sys, zipfile, re
from collections import Counter

from audit_native_elf import NativeElfError, validate_native_libraries

URL_RE = re.compile(rb'https?://[a-zA-Z0-9./?&=_:-]{6,120}')
FORBIDDEN_ENDPOINTS = (b'logs-sender-api.vercel.app',)

# Ordinary META-INF resources are outside the JAR/V1 coverage area by design.
# Keep only the exact runtime/provenance entries observed in the Release variant.
EXPECTED_META_INF_ENTRIES = frozenset((
    "META-INF/com/android/build/gradle/app-metadata.properties",
    "META-INF/services/kotlinx.coroutines.CoroutineExceptionHandler",
    "META-INF/services/kotlinx.coroutines.internal.MainDispatcherFactory",
))

REQUIRED_SERVICE_PROVIDERS = {
    "META-INF/services/kotlinx.coroutines.CoroutineExceptionHandler":
        "kotlinx.coroutines.android.AndroidExceptionPreHandler",
    "META-INF/services/kotlinx.coroutines.internal.MainDispatcherFactory":
        "kotlinx.coroutines.android.AndroidDispatcherFactory",
}


def validate_meta_inf_entries(archive):
    names = archive.namelist()
    meta_inf_entries = sorted(
        name for name in names
        if name.startswith("META-INF/") and not name.endswith("/")
    )

    duplicates = sorted(
        name for name, count in Counter(meta_inf_entries).items() if count > 1
    )
    if duplicates:
        raise ValueError("Duplicate META-INF entries: {}".format(", ".join(duplicates)))

    unexpected = sorted(set(meta_inf_entries) - EXPECTED_META_INF_ENTRIES)
    if unexpected:
        raise ValueError("Unexpected META-INF entries: {}".format(", ".join(unexpected)))

    for resource_name, expected_provider in REQUIRED_SERVICE_PROVIDERS.items():
        if resource_name not in names:
            raise ValueError("Missing required runtime ServiceLoader descriptor: {}".format(resource_name))
        try:
            descriptor = archive.read(resource_name).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("ServiceLoader descriptor is not valid UTF-8: {}".format(resource_name)) from exc

        providers = []
        for line in descriptor.splitlines():
            provider = line.split("#", 1)[0].strip()
            if provider:
                providers.append(provider)
        if providers != [expected_provider]:
            raise ValueError(
                "Unexpected ServiceLoader provider list in {}: {}".format(
                    resource_name, providers
                )
            )

    return meta_inf_entries


def audit(apk_path, min_api=21):
    print("=== VEYRAVAULT STAGE-2 COMPILED APK AUDIT: {} ===".format(apk_path))
    with zipfile.ZipFile(apk_path, 'r') as z:
        try:
            meta_inf_entries = validate_meta_inf_entries(z)
        except ValueError as exc:
            raise SystemExit("APK audit failed: {}".format(exc))

        print("Allow-listed META-INF resources retained in unsigned Release APK: {}".format(len(meta_inf_entries)))
        for entry in meta_inf_entries:
            print("  [EXPECTED-META-INF] {}".format(entry))
        print("All other META-INF resources remain rejected; signed Release separately verifies V1, V2 and V3.")

        try:
            native_results = validate_native_libraries(z, min_api)
        except NativeElfError as exc:
            raise SystemExit("APK native ELF audit failed: {}".format(exc))
        print("Native ELF ABI / API compatibility (application minSdk {}):".format(min_api))
        for path, label, metadata in native_results:
            print("  [NATIVE-ELF] {}: {}, Android API {}, NDK {} ({})".format(
                path, label, metadata["android_api"],
                metadata["ndk_version"], metadata["ndk_build"]
            ))

        libs = [n for n in z.namelist() if n.endswith('.so')]
        dexs = [n for n in z.namelist() if n.endswith('.dex')]
        print("Native C++ Virtualization Libraries (.so): {}".format(len(libs)))
        for lib in libs:
            print("  -", lib)
        print("Compiled DEX Bytecode Files: {}".format(len(dexs)))
        urls = set()
        forbidden = []
        for name in dexs + libs:
            data = z.read(name)
            for endpoint in FORBIDDEN_ENDPOINTS:
                if endpoint in data:
                    forbidden.append((name, endpoint.decode('ascii')))
            for match in URL_RE.findall(data):
                url = match.decode('utf-8', errors='ignore')
                if not any(x in url for x in ('schemas.android.com', 'apache.org', 'xmlpull.org', 'openstreetmap.org')):
                    urls.add(url)
        print("Embedded URLs in DEX/SO: {}".format(len(urls)))
        for url in sorted(urls):
            print("  [URL]", url)
        print("Forbidden remote log endpoints in APK: {}".format(len(forbidden)))
        for name, endpoint in forbidden:
            print("  [FORBIDDEN] {} -> {}".format(name, endpoint))
        if forbidden:
            raise SystemExit("APK audit failed: forbidden remote log-upload endpoint remains")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("apk")
    parser.add_argument("--min-api", type=int, default=21)
    args = parser.parse_args()
    audit(args.apk, args.min_api)
