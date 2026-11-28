#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "scripts" / "audit_source.py"


def run_audit(source_root):
    return subprocess.run(
        [sys.executable, str(AUDIT), str(source_root)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


with tempfile.TemporaryDirectory(prefix="veyravault-source-audit-") as temp:
    source_root = Path(temp)
    java_file = source_root / "Example.java"

    java_file.write_text(
        'final class Example { String endpoint = "https://example.invalid"; }\n',
        encoding="utf-8",
    )
    clean = run_audit(source_root)
    assert clean.returncode == 0, clean.stdout + clean.stderr
    assert "Forbidden remote log endpoints: 0" in clean.stdout

    java_file.write_text(
        'final class Example { String endpoint = "https://LOGS-SENDER-API.VERCEL.APP/send"; }\n',
        encoding="utf-8",
    )
    forbidden = run_audit(source_root)
    assert forbidden.returncode != 0, (
        "Forbidden remote log endpoint unexpectedly passed source audit.\n"
        + forbidden.stdout + forbidden.stderr
    )
    assert "[FORBIDDEN]" in forbidden.stdout
    assert "Source audit failed" in forbidden.stderr

print("PASS: Clean source passes and reports zero forbidden endpoints.")
print("PASS: Forbidden remote log endpoint is detected case-insensitively and fails the audit.")
