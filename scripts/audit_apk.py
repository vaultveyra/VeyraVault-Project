#!/usr/bin/env python3
import sys, zipfile, re

URL_RE = re.compile(rb'https?://[a-zA-Z0-9./?&=_:-]{6,120}')
FORBIDDEN_ENDPOINTS = (b'logs-sender-api.vercel.app',)

def audit(apk_path):
    print("=== VEYRAVAULT STAGE-2 COMPILED APK AUDIT: {} ===".format(apk_path))
    with zipfile.ZipFile(apk_path, 'r') as z:
        names = z.namelist()
        libs = [n for n in names if n.endswith('.so')]
        dexs = [n for n in names if n.endswith('.dex')]
        print("Native C++ Virtualization Libraries (.so): {}".format(len(libs)))
        for l in libs: print("  -", l)
        print("Compiled DEX Bytecode Files: {}".format(len(dexs)))
        urls = set()
        forbidden = []
        for n in dexs + libs:
            data = z.read(n)
            for endpoint in FORBIDDEN_ENDPOINTS:
                if endpoint in data:
                    forbidden.append((n, endpoint.decode('ascii')))
            for m in URL_RE.findall(data):
                u = m.decode('utf-8', errors='ignore')
                if not any(x in u for x in ('schemas.android.com', 'apache.org', 'xmlpull.org', 'openstreetmap.org')):
                    urls.add(u)
        print("Embedded URLs in DEX/SO: {}".format(len(urls)))
        for u in sorted(urls): print("  [URL]", u)
        print("Forbidden remote log endpoints in APK: {}".format(len(forbidden)))
        for name, endpoint in forbidden: print("  [FORBIDDEN] {} -> {}".format(name, endpoint))
        if forbidden:
            raise SystemExit("APK audit failed: forbidden remote log-upload endpoint remains")

if __name__ == '__main__':
    audit(sys.argv[1])
