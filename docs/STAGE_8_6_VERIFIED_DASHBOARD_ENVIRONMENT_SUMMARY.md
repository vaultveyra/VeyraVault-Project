# Stage 8.6 — Verified Dashboard environment summary

## Scope
- Preserve the live Tehran and New York clocks, Android host-device summary, and asynchronous Clone/Space counts.
- Add the current Android host-network transport and connectivity validation state.
- Read the last recorded Clone launch asynchronously and validate its exact packageName + userId against the strict Clone registry before displaying its effective profile.
- Resolve supported Locale, Time Zone, and location-policy fields independently using Clone > Global > System.
- Display stored Global brand/model/country/operator values only as metadata, with an explicit disclosure that the pinned Engine does not apply those values to cloned apps.
- Display public IP as Not checked. No external public-IP lookup is performed by the Dashboard.

## Correctness and privacy boundaries
- Host network state is not represented as a per-Clone route or proof of traffic tunneling.
- A detected Android VPN transport is only a host OS network observation; it does not prove that each virtual Clone uses that tunnel.
- Country/operator fields remain stored profile metadata and are not represented as the observed country, SIM state, carrier, or public IP.
- No IP address, VPN endpoint, ping, country, or carrier is fabricated.
- No external IP-check service is called. A future public-IP check must be explicitly user initiated and disclose the external request.
- Last-launch data is shown only when its composite packageName + userId identity is still present in the validated Clone registry.
- The Dashboard performs asynchronous reads only. It does not mutate CloneStore, stop a Clone, clear app data, uninstall a virtual package, or change account/session state.
- No permissions, manifest components, Engine behavior, Room schema, or migration state changed.

## Verification
- scripts/test_dashboard_verified_environment_summary.py checks host-only network labeling, truthful Public IP state, metadata disclosure, asynchronous profile reads, identity validation, per-field resolver use, and non-destructive behavior.
- The test is wired into .github/workflows/build-and-audit.yml.
- Existing Dashboard clock/device-info contract remains enabled.
- CI Android Instrumentation and release build/audit are required before declaring this stage CI-verified.
- Physical-device checks remain required for display accuracy and network transport behavior.
