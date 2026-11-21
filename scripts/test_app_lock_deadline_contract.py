from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
java_source = root / "app/src/main/java/com/veyravault/space/security/AppLockDeadline.java"
policy_source = (root / "app/src/main/java/com/veyravault/space/security/AppLockPolicy.java").read_text(encoding="utf-8")

harness = r"""
import com.veyravault.space.security.AppLockDeadline;

public final class AppLockDeadlineContractTest {
    private static void expect(long actual, long expected, String label) {
        if (actual != expected) throw new AssertionError(
                label + ": expected " + expected + " but got " + actual);
    }

    private static void expect(boolean actual, boolean expected, String label) {
        if (actual != expected) throw new AssertionError(
                label + ": expected " + expected + " but got " + actual);
    }

    private static void expectIllegalArgument(Runnable action, String label) {
        try {
            action.run();
            throw new AssertionError(label + ": expected IllegalArgumentException");
        } catch (IllegalArgumentException expected) {
            // Expected validation path.
        }
    }

    public static void main(String[] args) {
        expect(AppLockDeadline.timeoutMillis(0), 250L, "immediate transition grace");
        expect(AppLockDeadline.timeoutMillis(30), 30_000L, "30-second timeout");
        expect(AppLockDeadline.timeoutMillis(60), 60_000L, "1-minute timeout");
        expect(AppLockDeadline.timeoutMillis(300), 300_000L, "5-minute timeout");
        expect(AppLockDeadline.timeoutMillis(-1), 250L, "negative timeout fails closed");
        expect(AppLockDeadline.timeoutMillis(17), 250L, "unsupported timeout fails closed");
        expect(AppLockDeadline.timeoutMillis(301), 250L, "oversized timeout fails closed");

        long deadline = AppLockDeadline.deadlineAfter(10_000L, 30);
        expect(deadline, 40_000L, "monotonic deadline calculation");
        expect(AppLockDeadline.remainingMillis(deadline, 10_000L), 30_000L,
                "full timeout remaining");
        expect(AppLockDeadline.remainingMillis(deadline, 39_999L), 1L,
                "one millisecond before deadline");
        expect(AppLockDeadline.remainingMillis(deadline, 40_000L), 0L,
                "exact deadline boundary");
        expect(AppLockDeadline.remainingMillis(deadline, 45_000L), 0L,
                "deadline after device sleep");
        expect(AppLockDeadline.isExpired(deadline, 39_999L), false,
                "not expired before deadline");
        expect(AppLockDeadline.isExpired(deadline, 40_000L), true,
                "expired at deadline");
        expect(AppLockDeadline.isExpired(deadline, 45_000L), true,
                "expired after deep sleep elapsed time");
        expect(AppLockDeadline.remainingMillis(-1L, 45_000L), -1L,
                "missing deadline sentinel");
        expect(AppLockDeadline.isExpired(-1L, 45_000L), false,
                "missing deadline never expires");

        expect(AppLockDeadline.deadlineAfter(Long.MAX_VALUE - 100L, 30),
                Long.MAX_VALUE, "deadline addition saturates rather than overflows");
        expectIllegalArgument(() -> AppLockDeadline.deadlineAfter(-1L, 30),
                "negative deadline base");
        expectIllegalArgument(() -> AppLockDeadline.remainingMillis(100L, -1L),
                "negative current elapsed time");

        System.out.println("PASS: All supported app-lock timeout durations are exact.");
        System.out.println("PASS: Deadline boundaries and deep-sleep elapsed-time checks are correct.");
        System.out.println("PASS: Missing/unsupported values fail closed and overflow saturates.");
    }
}
"""
for marker in (
    "AppLockDeadline.TIMEOUT_IMMEDIATELY_SECONDS",
    "AppLockDeadline.TIMEOUT_30_SECONDS",
    "AppLockDeadline.TIMEOUT_1_MINUTE",
    "AppLockDeadline.TIMEOUT_5_MINUTES",
):
    assert marker in policy_source, f"Policy timeout is disconnected from deadline contract: {marker}"

with tempfile.TemporaryDirectory(prefix="veyravault-lock-deadline-") as temp:
    temp_path = Path(temp)
    harness_path = temp_path / "AppLockDeadlineContractTest.java"
    harness_path.write_text(harness, encoding="utf-8")
    compile_result = subprocess.run(
        ["javac", "-encoding", "UTF-8", "-d", str(temp_path),
         str(java_source), str(harness_path)],
        cwd=root, text=True, capture_output=True
    )
    if compile_result.returncode != 0:
        raise SystemExit(compile_result.stdout + compile_result.stderr)
    run_result = subprocess.run(
        ["java", "-cp", str(temp_path), "AppLockDeadlineContractTest"],
        cwd=root, text=True, capture_output=True
    )
    if run_result.returncode != 0:
        raise SystemExit(run_result.stdout + run_result.stderr)
    print(run_result.stdout, end="")
