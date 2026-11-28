# Stage 8.41 — Global Clone ID allocator rejected

Status: NOT IMPLEMENTED. The proposed global monotonic allocator was reviewed against the actual Spaces product model and rejected before release.

## Why it was rejected

In VeyraVault, `userId` is also the logical Space identity:
- `CloneEntry.getSpaceNumber()` returns `userId + 1`.
- `CloneStore.getGroupedBySpace()` groups entries by that Space number.
- `MainActivity` groups different package names into the same Space and derives the Engine userId from the Space number.
- Clone creation feedback displays the resulting Space number.

Therefore, two different app packages with the same numeric userId are not automatically a collision in the product model. They can be two apps installed inside the same logical Space. A global unique ID per Clone would assign each app a different userId, split apps across different Spaces, and break grouping, profile expectations and UI behavior.

## Decision

- Keep package-scoped userId allocation and existing Space numbering unchanged.
- Do not add a global high-water mark.
- Do not pass Engine inventories into CloneStore allocation.
- Do not remap, renumber or migrate any existing Clone.
- Keep Stage 8.39 numeric AccountManager diagnostics read-only.
- Keep Stage 8.40 findings: persistent AccountManager buckets are numeric-userId scoped; direct credential APIs do not currently apply package scope; persistent authTokens lack package identity.
- Resolve the AccountManager boundary inside the Engine rather than changing Space identity.

The attempted Stage 8.41 global allocator implementation was reverted from production code, tests and CI. No APK containing that allocator is approved for release.

## Required next stage

Stage 8.42 must design and test AccountManager storage/access keyed by trusted `(packageName, userId)`, preserving the existing shared Space number while separating per-package account credentials and persistent tokens. Legacy numeric buckets are ambiguous when multiple packages share one Space; they must not be split or deleted automatically.
