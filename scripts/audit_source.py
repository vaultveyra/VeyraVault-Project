#!/usr/bin/env python3
import os, re, sys

SUSPICIOUS_SDK = re.compile(r'(umeng|appsflyer|adjust\.sdk|flurry|admob|facebook\.ads|billingclient)', re.I)
URL_REGEX = re.compile(r'https?://[^\s"\'<>]+')

def scan(root):
    print("=== VEYRAVAULT STAGE-1 SOURCE AUDIT ===")
    urls, sdks, blobs = [], [], []
    for dp, _, files in os.walk(root):
        if '.git' in dp: continue
        for f in files:
            p = os.path.join(dp, f)
            if f.endswith(('.so', '.aar', '.dex', '.jar')):
                blobs.append(p)
            elif f.endswith(('.java', '.kt', '.xml', '.gradle', '.c', '.cpp')):
                try:
                    txt = open(p, errors='ignore').read()
                    for m in URL_REGEX.findall(txt):
                        if not any(w in m for w in ('schemas.android.com', 'apache.org', 'google.com', 'github.com', 'maven', 'gradle', 'openstreetmap')):
                            urls.append((p, m))
                    for m in SUSPICIOUS_SDK.findall(txt):
                        sdks.append((p, m))
                except Exception:
                    pass
    print("Binary blobs found: {}".format(len(blobs)))
    for b in blobs[:25]: print("  [BLOB]", b)
    print("Non-standard URLs found: {}".format(len(urls)))
    for p, u in urls[:30]: print("  [URL] {} -> {}".format(p, u))
    print("Suspicious SDK hits: {}".format(len(sdks)))
    for p, s in sdks: print("  [SDK-WARN] {} -> {}".format(p, s))

if __name__ == '__main__':
    scan(sys.argv[1] if len(sys.argv) > 1 else '.')
