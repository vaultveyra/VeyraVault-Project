# Stage 8.5.2 — Add App picker visual refinement

Date: 2026-11-19
Implementation commit: `172060b4bc1b03e332750450bd8db3e97f3dbd6e`
Contract/CI commits: `ffee8cb6c9ec46cc41573225524812582d5d1d6c`, `f4a5e055d962f6bf5958dc0ecf8c01bf96d7aa23`

## Change implemented

File: `app/src/main/java/com/veyravault/space/ui/AddAppActivity.java`

- Changed the installed-app picker from four columns to a less crowded three-column grid.
- Replaced fixed raw-pixel card spacing and app-icon dimensions with density-independent dp values.
- Reduced app icon tile size to 54dp and refined card padding/margins.
- Refined the header, batch action, search field and bottom batch-confirm spacing.
- Kept search single-line and retained the current app label/package filtering.

## Behavior preservation

The following existing operations remain in place: installed launcher-app discovery, duplicate package filtering, sorting, text search, batch selection, single-app clone flow, batch clone flow, safe user-ID reservation, Engine installation, and durable reservation commit/recovery. No CloneStore schema or clone/session data was changed.

## Regression guard

Added `scripts/test_add_app_picker_ui_contract.py` and wired it into CI. It checks the three-column density-aware grid and verifies the key app-discovery, search, single/batch clone and reservation/commit call sites remain present.

## Verification status

This is a source change plus a static contract test. Device rendering, accessibility review, RTL/LTR visual review and physical clone creation have not yet been performed. The CI Emulator environment previously failed to start (ADB TCP 5554 connection refused and emulator archive read error); the failure was infrastructure-level after all preceding source-contract steps passed. A rerun was requested, and the latest CI result must be checked before declaring this stage fully verified.
