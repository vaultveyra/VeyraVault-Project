# Stage 7.9.8 — Atomic Clone ID Reservation

## Status

Runtime implementation is committed on `feat/veyra-vault-product-foundation`. The final Stage 7.9.8 implementation and follow-up hardening were validated by PR run #478 (run ID `44384660038`) on commit `ff51482949a80b004cda65ab3c517cd3ef5c0708`: 37/37 Android Emulator instrumentation tests passed (0 skipped, 0 failed), Source Audit, unsigned release APK compilation, APK packaging/audit, artifact upload, and isolated signing all succeeded.

Target branch: `feat/veyra-vault-product-foundation`  
PR: #4 — keep Draft, open, and unmerged.

## Pre-implementation race

The previous `allocateNextUserId(packageName)` operation performed a lookup only. Its single-thread executor belonged to an individual repository instance, so two independent repository instances could both observe and return the same package-scoped ID before either Engine installation and registry write completed. An Activity-local guard did not close that race.

## Implemented reservation journal

- A versioned `pending_clone_reservations_json` key is stored in the existing `veyravault_clones_v2` SharedPreferences file. The legacy clone JSON schema and existing preference keys are preserved.
- Each reservation contains a UUID token, package name, and virtual user ID. The strict parser validates schema version, field types, non-empty identity/token values, and token/identity uniqueness. Unsupported, malformed, or conflicting journal data fails closed.
- `CloneStore.reserveNextUserId` reads the strict clone registry and journal, detects any registry/journal identity collision, selects the next unused package-scoped ID, and commits the reservation before returning it.
- A failed journal commit raises a dedicated persistence exception; `AsyncCloneRepository` maps it to `PERSISTENCE_FAILURE`. Malformed or inconsistent persisted data remains `CORRUPT_DATA`.
- Reservation acquisition and mutation APIs use static synchronization within the host application process. Separate repository instances in that process cannot reserve the same package/user identity concurrently.
- `commitReservedClone` verifies the exact token and package/user identity, then writes the clone registry and consumes only that reservation with one SharedPreferences Editor commit.
- Ordinary `upsertClone` and `saveAll` reject attempts to take a pending reservation's identity. The deprecated lookup-only allocator includes pending reservations but is not used in Engine-backed creation paths.
- Release requires positive Engine absence confirmation. `Engine.isCloneConfirmedAbsent` returns true only when the pinned Engine's installed-state query explicitly returns Boolean false; unknown/error/reflection-failure results retain the reservation.

## UI provisioning sequence

Both `AddAppActivity` and the MainActivity duplicate flow now follow:

1. Reserve the next package-scoped user ID and durably record its token.
2. Ask the Engine to install the virtual package for that identity.
3. Persist the clone record and consume the matching reservation in one commit.
4. On installation or registry failure, release only after Engine absence has been explicitly confirmed. If cleanup or Engine state is unknown, keep the reservation blocking reuse.

The repository has no Engine side effects; Engine checks remain in the UI/Engine layer. Clone records are not written before Engine installation succeeds.

## Validation coverage

Reservation-specific instrumentation covers:
- two independent repository instances racing to reserve IDs for the same package;
- persistence across repository close/recreation and exact-token consumption;
- rejection of mismatched package/user/token use;
- refusal to release without positive Engine absence, followed by safe release and reuse;
- prevention of an ordinary upsert stealing a pending identity;
- fail-closed handling of malformed journals and registry/journal identity conflicts;
- classification of a reservation-journal commit failure as `PERSISTENCE_FAILURE`.

Run #478 on the final Stage 7.9.8 commit validated 37/37 Android Emulator tests, 0 skipped and 0 failed, Source Audit, unsigned Release build, APK package/audit and artifact upload. Artifacts:
- [Signed release](https://github.com/vaultveyra/VeyraVault-Project/actions/runs/44384660038/artifacts/14466347687), ID `14466347687`, ZIP digest `sha256:385d61069c6cf0ec1892fdf7ab25e4d8a081e6a6c658b586decf5121fef92190`.
- [Unsigned build and audit reports](https://github.com/vaultveyra/VeyraVault-Project/actions/runs/44384660038/artifacts/14466017924), ID `14466017924`, ZIP digest `sha256:87b77ca84d16b19cde01dccf823b299086d4b24d0d2d5de29c4552b6365e8e97`.

## Scope and limitations

- **Process scope:** static synchronization coordinates callers inside the VeyraVault host app process only. Android SharedPreferences is not a cross-process lock, and this implementation does not claim multi-process writer safety. The clone-provisioning Activities are in the default host process; concurrent multi-process provisioning remains unsupported.
- **Restart handling:** the journal is durable and survives host-process recreation. Tests close/recreate Repository instances; there is no dedicated OS-kill test for the clone-provisioning sequence itself.
- **Orphan recovery:** if the host process dies after Engine installation but before registry commit, the journal conservatively keeps the ID blocked. There is no automatic startup reconciler or user-facing orphan-reservation repair UI yet. An unknown Engine state must continue to block reuse.
- **Device validation:** physical-device concurrency, interrupted-install recovery, Engine reflection compatibility, and third-party app/session regression testing remain outstanding.
- **No migration/cutover:** Room remains inactive and is not used for this reservation path. SharedPreferences/CloneStore remains the runtime source of truth.

## Explicit non-goals

- No Room runtime activation, persistence migration, or cutover.
- No automatic deletion of virtual packages or clone data.
- No export, restore, or modification of third-party app data, accounts, or sessions.
- No startup behavior change or automatic orphan cleanup.
- No direct modification of `main`; PR #4 remains open and Draft, and must not be merged as part of this stage.
