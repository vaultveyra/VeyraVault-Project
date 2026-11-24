from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = (root / "app/src/main/java/com/veyravault/space/ui/MainActivity.java").read_text(encoding="utf-8")

assert "AsyncCloneRepository.getInstance(getApplicationContext())" in source
assert "repository.loadClones" in source
assert "repository.loadCollapsedSpaces" in source
assert "repository.setSpaceCollapsed" in source
assert "repository.loadGlobalEnvironment" in source
on_resume = source[source.index("protected void onResume()"):source.index("private void buildDashboardUi()")]
assert "loadGlobalProfileSummary()" in on_resume
assert "CloneStore.getGroupedBySpace" not in source
assert "CloneStore.isSpaceCollapsed" not in source
assert "CloneStore.setSpaceCollapsed" not in source
assert "CloneStore.getGlobalEnv" not in source
assert "buildSpaceCard(entry.getKey(), entry.getValue()," in source
assert "collapsedSpaces.contains(entry.getKey())" in source

refresh = source[source.index("private void refreshSpaces()"):source.index("private boolean isCurrentRefresh")]
assert refresh.index("repository.loadClones") < refresh.index("repository.loadCollapsedSpaces")
assert refresh.index("if (!cloneResult.isSuccess())") < refresh.index("spacesContainer.removeAllViews()")
assert "Preserve the last known UI" in refresh
assert "Do not silently expand every Space" in refresh

header_start = source.index("header.setOnClickListener(v -> {")
header_end = source.index("card.addView(header);", header_start)
header = source[header_start:header_end]
assert "repository.setSpaceCollapsed" in header
assert header.index("if (result.isSuccess())") < header.index("refreshSpaces()")
assert "Space collapse state was not saved" in header

toggle_start = source.index("private void toggleAllSpaces()")
toggle_end = source.index("private void finishToggleAllWithFailure", toggle_start)
toggle = source[toggle_start:toggle_end]
assert "repository.loadClones" in toggle
assert "repository.loadCollapsedSpaces" in toggle
assert "setAllSpacesCollapsed(spaceNumbers, !allCollapsed, 0)" in toggle
assert "repository.setSpaceCollapsed" in toggle
assert "some earlier changes may already be saved" in source

# Clone creation is delegated to the shared transaction coordinator, not run in UI callbacks.
assert "duplicateCloneWithPreflight(item);" in source
assert "private void duplicateCloneWithPreflight(final CloneStore.CloneEntry item)" in source
assert "provisionRepository.createClone(item.packageName, item.displayName, fa" in source
assert "Engine.installPackageAsUser(" not in source
assert "Engine.isCloneConfirmedAbsent(" not in source
assert "EngineOperationQueue.submit(" in source
assert "Engine.uninstallClone(item.packageName, item.userId)" in source
assert "Engine.uninstallClone(entry.packageName, entry.userId)" in source

print("PASS: MainActivity uses strict asynchronous repository reads for Spaces and global profile summary.")
print("PASS: Collapse/expand actions are commit-aware and preserve the last rendered UI on read failure.")
print("PASS: Clone provisioning and uninstall work are delegated to the shared Engine operation queue.")
