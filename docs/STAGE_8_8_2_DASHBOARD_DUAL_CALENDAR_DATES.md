# Stage 8.8.2 — Tehran Jalali and New York Gregorian Dashboard dates

## Product behavior
- Tehran card displays live local time in a fixed 12-hour format and the Jalali calendar date.
- New York card displays live local time in a fixed 12-hour format and the Gregorian calendar date.
- Both cards use explicit IANA zones: `Asia/Tehran` and `America/New_York`; neither changes the Android device zone or any Clone profile.
- Persian UI localizes date digits; English UI uses ASCII digits.
- Date labels refresh with TextClock minute ticks and are initialized immediately when Dashboard is created.

## Calendar correctness
- Add a pure-Java Jalali converter with no new runtime dependency and no Android API-level dependency.
- Automated test compiles and executes the production Java formatter directly with `javac`/ `java`.
- Cover Nowruz boundaries, leap-year Esfand 30, non-leap Esfand 29, Tehran-vs-New-York date rollover, and Persian digit localization.

## Safety and compatibility
- No CloneStore, Engine, package/user identity, profile, account/session, VPN, manifest, permission, Room schema, or migration changes.
- No network calls or third-party calendar service.
- Existing live TextClock time-zone separation and device metadata remain intact.
- The date utility is additive and uses only Java standard-library APIs available at the app minimum SDK.

## Verification
- `scripts/test_dashboard_date_format_contract.py` compiles and executes the production formatter and checks Dashboard wiring.
- The script is part of GitHub Actions before Android Emulator startup.
- CI Android instrumentation, release build, source audit and APK audit remain required on the exact commit.
- Physical-device visual validation in Persian RTL and English LTR remains outstanding.
