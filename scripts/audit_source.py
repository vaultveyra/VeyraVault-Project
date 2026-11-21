#!/usr/bin/env python3
import os
import re
import sys

SUSPICIOUS_SDK = re.compile(r'(umeng|appsflyer|adjust\\.sdk|flurry|admob|facebook\\.ads|billingclient)', re.I)
URL_REGEX = re.compile(r'https?://[^\\s"\\'<>]+')
FORBIDDEN_ENDPOINTS = ("logs-sender-api.vercel.app",)


def scan(root):
    print("=== VEYRAVAULT STAGE-1 SOURCE AUDIT ===")
    urls, sdks, blobs, forbidden = [], [], [], []
    for dp, _, files in os.walk(root):
        if '.git' in dp:
            continue
        for filename in files:
            path = os.path.join(dp, filename)
            if filename.endswith(('.so', '.aar', '.dex', '.jar')):
                blobs.append(path)
            elif filename.endswith(('.java', '.kt', '.xml', '.gradle', '.c', '.cpp')):
                try:
                    with open(path, encoding='utf-8', errors='ignore') as source_file:
                        source = source_file.read()
                except OSError as error:
                    raise SystemExit("Source audit could not read {}: {}".format(path, error))

                for match in URL_REGEX.findall(source):
                    if not any(
                        allowed in match
                        for allowed in (
                            'schemas.android.com', 'apache.org', 'google.com',
                            'github.com', 'maven', 'gradle', 'openstreetmap'
                        )
                    ):
                        urls.append((path, match))

                lowered_source = source.lower()
                for endpoint in FORBIDDEN_ENDPOINTS:
                    if endpoint.lower() in lowered_source:
                        forbidden.append((path, endpoint))

                for match in SUSPICIOUS_SDK.findall(source):
                    sdks.append((path, match))

    print("Binary blobs found: {}".format(len(blobs)))
    for blob in blobs[:25]:
        print("  [BLOB]", blob)
    print("Non-standard URLs found: {}".format(len(urls)))
    for path, url in urls[:30]:
        print("  [URL] {} -> {}".format(path, url))
    print("Suspicious SDK hits: {}".format(len(sdks)))
    for path, sdk in sdks:
        print("  [SDK-WARN] {} -> {}".format(path, sdk))
    print("Forbidden remote log endpoints: {}".format(len(forbidden)))
    for path, endpoint in forbidden:
        print("  [FORBIDDEN] {} -> {}".format(path, endpoint))
    if forbidden:
        raise SystemExit("Source audit failed: forbidden remote log-upload endpoint remains")


if __name__ == '__main__':
    scan(sys.argv[1] if len(sys.argv) > 1 else '.')
