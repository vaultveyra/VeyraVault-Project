#!/usr/bin/env python3
import os
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JAVA_ROOT = os.path.join(ROOT, "app", "src", "main", "java")
SOURCES = [
    os.path.join(JAVA_ROOT, "com", "veyravault", "space", "core", "ProfileSettings.java"),
    os.path.join(JAVA_ROOT, "com", "veyravault", "space", "core", "ProfileResolver.java"),
    os.path.join(ROOT, "scripts", "ProfileResolverContractTest.java"),
]

with tempfile.TemporaryDirectory(prefix="veyra-profile-tests-") as output:
    subprocess.run(["javac", "-encoding", "UTF-8", "-d", output] + SOURCES, check=True)
    subprocess.run(["java", "-cp", output, "ProfileResolverContractTest"], check=True)
