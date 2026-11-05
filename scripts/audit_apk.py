#!/usr/bin/env python3
import sys, zipfile, re

URL_RE = re.compile(rb'https?://[a-zA-Z0-9./?&=_:-]{6,120}')

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
        for n in dexs + libs:
            data = z.read(n)
            for m in URL_RE.findall(data):
                u = m.decode('utf-8', errors='ignore')
                if not any(x in u for x in ('schemas.android.com', 'apache.org', 'xmlpull.org', 'openstreetmap.org')):
                    urls.add(u)
        print("Embedded URLs in DEX/SO: {}".format(len(urls)))
        for u in sorted(urls): print("  [URL]", u)

if __name__ == '__main__':
    audit(sys.argv[1])
