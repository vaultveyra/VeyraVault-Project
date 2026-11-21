# Stage 8.5.3 — Spaces cards and clone grid refinement

Date: 2026-11-19
Implementation commit: `106d770c544f5deee5cb1c5976d2838a7d41fd37`
Contract/CI commits: `cdce0553e81e1019bf2c69030d5cf5d38f13704a`, `e60c004cb155f949c50706ee413b4785ac5007b8`

## Changes

File: `app/src/main/java/com/veyravault/space/ui/MainActivity.java`

- Reduced Space card padding and inter-card spacing; added subtle elevation.
- Reduced collapsed preview app icons to 28dp.
- Changed the expanded clone grid to three columns with density-aware cell sizing.
- Reduced clone app icon frames to 64dp and refined cell/label spacing.
- Converted updated dimensions and margins to density-independent dp units.

## Preserved behavior

- Space collapse/expand still uses the existing asynchronous repository call.
- GMS enabled-state read and toggle remain wired to the existing Engine methods.
- Clone launch still uses `AsyncCloneLaunchRepository.launchClone`.
- Clone configuration bottom sheet remains reachable from each clone cell.
- No CloneStore/session/account payload, package/user mapping, engine, or Room behavior changed.

## Regression guard

Added `scripts/test_spaces_cards_ui_contract.py` and wired it into CI. It checks preserved collapse/GMS/async-launch/configuration paths and the new compact dimensions.

## Verification status

Source contract added; CI outcome pending. No physical-device visual review or clone interaction validation has been performed. The preceding CI runs failed at Android Emulator boot (device `emulator-5554` not found / boot timeout), not at the source-contract steps. A passing emulator run is still required before the UI slice is fully verified.
