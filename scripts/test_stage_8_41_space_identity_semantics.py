#!/usr/bin/env python3
"""Guard the product invariant that virtual userId is also the user-facing Space ID."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STORE = (ROOT / "app/src/main/java/com/veyravault/space/core/CloneStore.java").read_text(encoding="utf-8")
MAIN = (ROOT / "app/src/main/java/com/veyravault/space/ui/MainActivity.java").read_text(encoding="utf-8")
ADD = (ROOT / "app/src/main/java/com/veyravault/space/ui/AddAppActivity.java").read_text(encoding="utf-8")
PROVISION = (ROOT / "app/src/main/java/com/veyravault/space/core/AsyncCloneProvisionRepository.java").read_text(encoding="utf-8")

start = STORE.index("public int getSpaceNumber()")
end = STORE.index("}", start)
assert "return userId + 1;" in STORE[start:end]
assert "int spaceNum = e.getSpaceNumber();" in STORE
assert "grouped.get(spaceNumber).add(clone);" in MAIN
assert "final int uid = spaceNum - 1;" in MAIN
assert "outcome.clone.getSpaceNumber()" in ADD

signature_start = STORE.index("static synchronized CloneReservation reserveNextUserId(")
signature_end = STORE.index("{", signature_start)
signature = STORE[signature_start:signature_end]
assert "String packageName" in signature
assert "List<Integer> engineUserIds" not in signature
assert "KEY_GLOBAL_HIGH_WATER_MARK" not in STORE

reserve_end = STORE.index("static synchronized List<CloneReservation>", signature_start)
reserve = STORE[signature_start:reserve_end]
assert "packageName.equals(entry.packageName)" in reserve
assert "packageName.equals(reservation.packageName)" in reserve
assert "int candidate = 0;" in reserve
assert "persistence.reserveNextUserId(packageName, allocation ->" in PROVISION
assert "Engine.getKnownVirtualUserIds()" not in PROVISION
assert "Engine.getKnownAccountUserIds()" not in PROVISION

print("PASS: userId remains the stable Space identity displayed as userId + 1.")
print("PASS: MainActivity groups different app packages under the same logical Space number.")
print("PASS: Clone allocation remains package-scoped; a global per-Clone ID would break Spaces.")
print("PASS: Stage 8.40 AccountManager scope investigation remains separate from Space numbering.")
