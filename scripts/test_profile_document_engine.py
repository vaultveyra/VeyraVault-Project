#!/usr/bin/env python3
import os
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JAVA_ROOT = os.path.join(ROOT, "app", "src", "main", "java", "com", "veyravault", "space", "core")
SOURCES = [
    os.path.join(JAVA_ROOT, "ProfileFieldRegistry.java"),
    os.path.join(JAVA_ROOT, "ProfileDocument.java"),
    os.path.join(JAVA_ROOT, "ProfileDocumentResolver.java"),
    os.path.join(ROOT, "scripts", "ProfileDocumentContractTest.java"),
]
with tempfile.TemporaryDirectory(prefix="veyra-profile-document-") as output:
    subprocess.run(["javac", "-encoding", "UTF-8", "-d", output] + SOURCES, check=True)
    subprocess.run(["java", "-cp", output, "ProfileDocumentContractTest"], check=True)
