import com.veyravault.space.security.AppLockAttemptPolicy;

public final class AppLockAttemptPolicyTest {
    private static void check(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }

    public static void main(String[] args) {
        int failures = 0;
        for (int i = 1; i <= AppLockAttemptPolicy.UNTHROTTLED_FAILURES; i++) {
            failures = AppLockAttemptPolicy.nextFailureCount(failures);
            check(AppLockAttemptPolicy.lockoutDurationMillis(failures) == 0L,
                    "first four failures must not start a cooldown");
        }

        failures = AppLockAttemptPolicy.nextFailureCount(failures);
        check(failures == 5, "fifth failure count");
        check(AppLockAttemptPolicy.lockoutDurationMillis(failures)
                == AppLockAttemptPolicy.FIRST_LOCKOUT_MILLIS, "fifth failure cooldown");

        failures = AppLockAttemptPolicy.nextFailureCount(failures);
        check(AppLockAttemptPolicy.lockoutDurationMillis(failures)
                == AppLockAttemptPolicy.SECOND_LOCKOUT_MILLIS, "sixth failure cooldown");

        failures = AppLockAttemptPolicy.nextFailureCount(failures);
        check(AppLockAttemptPolicy.lockoutDurationMillis(failures)
                == AppLockAttemptPolicy.THIRD_LOCKOUT_MILLIS, "seventh failure cooldown");

        failures = AppLockAttemptPolicy.nextFailureCount(failures);
        check(AppLockAttemptPolicy.lockoutDurationMillis(failures)
                == AppLockAttemptPolicy.MAX_LOCKOUT_MILLIS, "eighth failure reaches cap");

        check(AppLockAttemptPolicy.lockoutDurationMillis(Integer.MAX_VALUE)
                == AppLockAttemptPolicy.MAX_LOCKOUT_MILLIS, "cooldown is always bounded");
        check(AppLockAttemptPolicy.nextFailureCount(Integer.MAX_VALUE)
                == AppLockAttemptPolicy.MAX_TRACKED_FAILURES, "failure counter saturates");
        check(AppLockAttemptPolicy.nextFailureCount(-1)
                == AppLockAttemptPolicy.MAX_TRACKED_FAILURES, "negative counter fails closed");

        long deadline = AppLockAttemptPolicy.deadlineMillis(5, 1_000L);
        check(deadline == 31_000L, "deadline calculation");
        check(AppLockAttemptPolicy.remainingMillis(deadline, 1_000L) == 30_000L,
                "remaining cooldown before deadline");
        check(AppLockAttemptPolicy.remainingMillis(deadline, 31_000L) == 0L,
                "cooldown expires exactly at deadline");
        check(AppLockAttemptPolicy.deadlineMillis(4, 1_000L) == 0L,
                "no deadline before threshold");
        check(AppLockAttemptPolicy.deadlineMillis(5, Long.MAX_VALUE - 10L)
                == Long.MAX_VALUE, "deadline addition must not overflow");

        System.out.println("AppLockAttemptPolicy tests: PASS");
    }
}
