# Stage 8.5.4 — Dashboard city clocks and device summary

Date: 2026-11-19
Implementation commit: `13645ed9ed586c5b88f1d63caab82789d31763a6`
Contract/CI commits: `f8639776ff4998b69ff3526026b4b0c779126a31`, `5846061706d8026bf89eda8f2f82f300c1d982fb`

## Changes

File: `app/src/main/java/com/veyravault/space/ui/DashboardActivity.java`

- Added live Tehran clock using Android `TextClock` with `Asia/Tehran`.
- Added live New York clock using Android `TextClock` with `America/New_York`.
- Both clocks display seconds and respect the user's 12/24-hour system preference.
- Added a device summary using Android platform fields: manufacturer, model and Android release.
- Added compact density-independent card spacing.

## Preserved behavior

- Clone and Space counts still load asynchronously from the existing Clone registry.
- Existing Dashboard navigation to Spaces, Add App, VPN Status and Settings remains unchanged.
- No IP address is fabricated or displayed. This slice does not implement public-IP lookup.
- VPN status remains the existing read-only Android system VPN transport indicator.
- No Clone/session/account data, profile payload, manifest, network configuration or Room migration changed.

## Regression guard

Added `scripts/test_dashboard_clocks_device_info_contract.py` and wired it into CI. It verifies the explicit time-zone IDs, platform TextClock usage, Android Build device fields and existing dashboard navigation/registry calls.

## Verification status

Static source contract is added; CI and Android Emulator results are pending. The preceding workflow runs failed while starting the hosted emulator (emulator-5554 missing / boot timeout). No physical-device rendering or clock accuracy review has yet been completed.
