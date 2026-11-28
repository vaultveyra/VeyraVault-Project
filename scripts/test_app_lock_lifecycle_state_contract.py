from pathlib import Path
import subprocess
import tempfile
root = Path(__file__).resolve().parents[1]
sources = [
    root / "app/src/main/java/com/veyravault/space/security/AppLockDeadline.java",
    root / "app/src/main/java/com/veyravault/space/security/AppLockLifecycleState.java",
]
harness = r"""
import com.veyravault.space.security.AppLockLifecycleState;
public final class AppLockLifecycleStateContractTest {
    private static void b(boolean a, boolean e, String l) { if (a != e) throw new AssertionError(l + ": expected " + e + " but got " + a); }
    private static void n(long a, long e, String l) { if (a != e) throw new AssertionError(l + ": expected " + e + " but got " + a); }
    private static void i(int a, int e, String l) { if (a != e) throw new AssertionError(l + ": expected " + e + " but got " + a); }
    public static void main(String[] args) {
        AppLockLifecycleState s = new AppLockLifecycleState();
        b(s.onActivityStarted(1000L, true), false, "initial activity");
        b(s.onActivityStarted(1010L, true), false, "second activity");
        i(s.getStartedActivityCount(), 2, "two activity count");
        b(s.onActivityStopped(), false, "first stop does not background app");
        b(s.onActivityStopped(), true, "last stop backgrounds app");
        n(s.beginBackgroundDeadline(2000L, 30, true), 32000L, "background deadline");
        b(s.onActivityStarted(31999L, true), false, "return before deadline");
        n(s.getBackgroundDeadlineElapsedRealtime(), -1L, "early return clears deadline");
        b(s.onActivityStopped(), true, "leave again");
        s.beginBackgroundDeadline(40000L, 30, true);
        b(s.onActivityStarted(70000L, true), true, "return after deadline");
        n(s.getBackgroundDeadlineElapsedRealtime(), -1L, "expired return clears deadline");
        b(s.onActivityStopped(), true, "leave with lock disabled");
        s.beginBackgroundDeadline(80000L, 60, true);
        b(s.onActivityStarted(100000L, false), false, "disabled lock never locks");
        n(s.getBackgroundDeadlineElapsedRealtime(), -1L, "disabled lock clears deadline");
        b(s.onActivityStopped(), true, "leave before configuration recreation");
        s.beginBackgroundDeadline(110000L, 30, true);
        s.clearBackgroundDeadline();
        b(s.onActivityStarted(150000L, true), false, "configuration recreation does not lock");
        i(s.getStartedActivityCount(), 1, "configuration restores count");
        b(s.onActivityStopped(), true, "final cleanup");
        b(s.onActivityStopped(), true, "duplicate stop remains at zero");
        i(s.getStartedActivityCount(), 0, "count never negative");
        System.out.println("PASS: Multi-Activity transitions and final-Activity background detection.");
        System.out.println("PASS: Return before deadline cancels lock; return after deadline locks.");
        System.out.println("PASS: Disabled lock and configuration recreation do not lock the session.");
        System.out.println("PASS: Activity count remains bounded at zero.");
    }
}
"""
with tempfile.TemporaryDirectory(prefix="veyravault-lock-lifecycle-") as temp:
    temp_path = Path(temp)
    harness_path = temp_path / "AppLockLifecycleStateContractTest.java"
    harness_path.write_text(harness, encoding="utf-8")
    compile_result = subprocess.run(
        ["javac", "-encoding", "UTF-8", "-d", str(temp_path), *map(str, sources), str(harness_path)],
        cwd=root, text=True, capture_output=True)
    if compile_result.returncode != 0:
        raise SystemExit(compile_result.stdout + compile_result.stderr)
    run_result = subprocess.run(
        ["java", "-cp", str(temp_path), "AppLockLifecycleStateContractTest"],
        cwd=root, text=True, capture_output=True)
    if run_result.returncode != 0:
        raise SystemExit(run_result.stdout + run_result.stderr)
    print(run_result.stdout, end="")
