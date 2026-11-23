#!/usr/bin/env python3
import os
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JAVA_ROOT = os.path.join(ROOT, "app", "src", "main", "java")
SOURCES = [
    os.path.join(JAVA_ROOT, "com", "veyravault", "space", "security", "SecurityCredentialHasher.java"),
    os.path.join(JAVA_ROOT, "com", "veyravault", "space", "security", "AppLockAttemptPolicy.java"),
    os.path.join(ROOT, "scripts", "SecurityCredentialHasherTest.java"),
    os.path.join(ROOT, "scripts", "AppLockAttemptPolicyTest.java"),
]

with tempfile.TemporaryDirectory(prefix="veyra-security-tests-") as output:
    subprocess.run(["javac", "-encoding", "UTF-8", "-d", output] + SOURCES, check=True)
    subprocess.run(["java", "-cp", output, "SecurityCredentialHasherTest"], check=True)
    subprocess.run(["java", "-cp", output, "AppLockAttemptPolicyTest"], check=True)
