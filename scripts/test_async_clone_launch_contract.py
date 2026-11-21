from pathlib import Path

engine = Path("app/src/main/java/com/veyravault/space/core/Engine.java").read_text(encoding="utf-8")
launch = engine[engine.index("public static CloneLaunchResult launchCloneDetailed"):engine.index("public static void stopClone")]
assert "VirtualHookManager.syncCloneHooks(ctx, entry)" in launch
assert launch.index("VirtualHookManager.syncCloneHooks(ctx, entry)") < launch.index('getMethod("launchApk"')
assert launch.index('getMethod("launchApk"') < launch.index("CloneStore.recordActiveLaunch(ctx, entry)")
assert "public static boolean launchClone(Context ctx, CloneStore.CloneEntry entry)" in launch

repository = Path("app/src/main/java/com/veyravault/space/core/AsyncCloneLaunchRepository.java").read_text(encoding="utf-8")
assert "Executors.newSingleThreadExecutor()" in repository
assert "CloneStore.readAllStrict(appContext)" in repository
assert "Engine.launchCloneDetailed(appContext, target)" in repository
assert "mainHandler.post(() -> callback.onComplete(outcome))" in repository
assert "CLONE_NOT_FOUND_IN_STRICT_REGISTRY" in repository

main = Path("app/src/main/java/com/veyravault/space/ui/MainActivity.java").read_text(encoding="utf-8")
assert "AsyncCloneLaunchRepository.getInstance(getApplicationContext())" in main
assert "launchRepository.launchClone(pkg, uid" in main
assert "launchRepository.launchClone(item.packageName, item.userId" in main
assert "showCloneLaunchFeedback(outcome" in main
assert "Engine.launchClone(" not in main
assert "VirtualHookManager.syncCloneHooks(" not in main

print("PASS: Dashboard and shortcut launches run on a serialized worker; strict registry lookup and location hook synchronization precede Engine launch, with separate hook outcome feedback.")
