#!/usr/bin/env python3
"""Contracts for preparing KVM before Android emulators and avoiding duplicate PR builds."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github/workflows/build-and-audit.yml").read_text(encoding="utf-8")
doc = ROOT / "docs/STAGE_8_32_EMULATOR_KVM_READINESS.md"

# Feature branch commits are validated by the PR event; main pushes retain their own build.
assert 'push:\n    branches: [ "main" ]' in workflow
assert 'pull_request:\n    branches: [ "main" ]' in workflow
trigger_section = workflow.split("on:", 1)[1].split("permissions:", 1)[0]
assert '"feat/veyra-vault-product-foundation"' not in trigger_section

kvm_step = workflow.find("- name: Enable KVM for Android Emulator")
api34_step = workflow.find("- name: Run Room Android instrumentation tests")
api21_step = workflow.find("- name: Run Android API 21 legacy compatibility smoke tests")
assert kvm_step >= 0 and api34_step > kvm_step and api21_step > kvm_step

for marker in (
    "/dev/kvm",
    "99-kvm4all.rules",
    'GROUP="kvm"',
    'MODE="0666"',
    "sudo udevadm control --reload-rules",
    "sudo udevadm trigger --name-match=kvm",
    "KVM is readable and writable",
    "will use TCG",
    "disable-linux-hw-accel: auto",
    'ANDROID_I_WANT_MY_TCG: "yes"',
):
    assert marker in workflow, "Missing emulator readiness control: " + marker

assert workflow.count('ANDROID_I_WANT_MY_TCG: "yes"') == 2
assert workflow.count("disable-linux-hw-accel: auto") == 2
assert workflow.count("emulator-boot-timeout: 1200") == 2
assert doc.is_file()

print("PASS: KVM permission setup runs before both emulator jobs.")
print("PASS: The runner reports explicit hardware-acceleration or TCG fallback state.")
print("PASS: TCG opt-in and automatic KVM detection remain configured for API 34 and API 21.")
print("PASS: PR feature commits are validated once by pull_request; main push builds remain enabled.")
