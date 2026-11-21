# Stage 8.5.1 — Spaces bottom navigation refinement

Date: 2026-11-19
Implementation commit: `c99e38cd0f7d5481ed15ecba33a0fea922c43730`
Contract/CI commits: `df7085dbedc5d9616e36db6ce63f0e84dc76b68c`, `62f0e0d2e501f1d4c007a070f948d9c60e202657`

## Change implemented

File: `app/src/main/java/com/veyravault/space/ui/MainActivity.java`

- Replaced text-only bottom navigation controls with compact vertical icon + label items.
- Preserved all existing destinations/actions: Dashboard, Spaces refresh, Add App, VPN status, Settings.
- Added accessible content descriptions to navigation items and the Add App action.
- Replaced the 132 x 132 raw-pixel text-plus control with a density-independent 48dp ImageView add action.
- Added a local dp conversion helper and used density-independent spacing/sizing for the updated navigation area.
- Retained existing click handlers and asynchronous clone repository/launch flows.

Icons currently use Android framework drawable resources as a safe first implementation. A later design pass should replace them with a consistent branded vector icon set after visual review.

## Regression guard

Added `scripts/test_spaces_bottom_navigation_ui_contract.py` and wired it into `.github/workflows/build-and-audit.yml`. It asserts the five destinations remain present, the navigation items are icon-led and accessible, and the add target is 48dp rather than the previous oversized 132px control.

## Scope and limitations

- This is a focused Spaces bottom-navigation refinement, not a complete redesign of Dashboard, Spaces cards, Add App, Settings or VPN.
- No clone registry, package/user identity, session, account, app-private data, profile payload, manifest, engine dependency or Room migration was changed.
- No device rendering or physical-device interaction has been verified yet.
- Android framework icons are functional placeholders, not the final branded visual design.
- CI runs for this commit and its contract test must pass before treating this slice as verified.
