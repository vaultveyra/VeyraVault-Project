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

        check(AppLockAttemptPolicy.isPersistedAttemptStateConsistent(0, 0L),
                "empty attempt state is consistent");
        check(AppLockAttemptPolicy.isPersistedAttemptStateConsistent(4, 0L),
                "unthrottled attempts must not have a deadline");
        check(AppLockAttemptPolicy.isPersistedAttemptStateConsistent(5, 31_000L),
                "throttled attempts must retain a deadline");
        check(!AppLockAttemptPolicy.isPersistedAttemptStateConsistent(5, 0L),
                "throttled count without deadline is malformed");
        check(!AppLockAttemptPolicy.isPersistedAttemptStateConsistent(4, 31_000L),
                "unthrottled count with deadline is malformed");
        check(!AppLockAttemptPolicy.isPersistedAttemptStateConsistent(0, 31_000L),
                "empty count with deadline is malformed");
        check(!AppLockAttemptPolicy.isPersistedAttemptStateConsistent(-1, 0L),
                "negative failure count is malformed");

        long elapsedDeadline = AppLockAttemptPolicy.initializeElapsedDeadline(
                AppLockAttemptPolicy.ELAPSED_DEADLINE_UNINITIALIZED,
                deadline, 1_000L, 5_000L);
        check(elapsedDeadline == 35_000L, "wall deadline is converted to elapsed time once");
        long afterBackwardWallClockShift = AppLockAttemptPolicy.initializeElapsedDeadline(
                elapsedDeadline, deadline, -50_000L, 15_000L);
        check(afterBackwardWallClockShift == elapsedDeadline,
                "backwards wall-clock changes must not reset the elapsed deadline");
        check(AppLockAttemptPolicy.remainingMillis(afterBackwardWallClockShift, 15_000L)
                == 20_000L, "elapsed cooldown continues across a wall-clock rollback");

        check(AppLockAttemptPolicy.boundedRemainingMillis(Long.MAX_VALUE, 1_000L)
                == AppLockAttemptPolicy.MAX_LOCKOUT_MILLIS,
                "persisted wall-clock deadlines cannot exceed the 15-minute maximum");
        long boundedElapsedDeadline = AppLockAttemptPolicy.initializeElapsedDeadline(
                AppLockAttemptPolicy.ELAPSED_DEADLINE_UNINITIALIZED,
                Long.MAX_VALUE, 1_000L, 5_000L);
        check(boundedElapsedDeadline == 905_000L,
                "fresh process reconstructs a far-future persisted deadline with the cap");
        check(AppLockAttemptPolicy.initializeElapsedDeadline(
                AppLockAttemptPolicy.ELAPSED_DEADLINE_UNINITIALIZED,
                999L, 1_000L, 5_000L)
                == AppLockAttemptPolicy.ELAPSED_DEADLINE_NONE,
                "expired wall deadline initializes to no active deadline");
        check(AppLockAttemptPolicy.initializeElapsedDeadline(
                AppLockAttemptPolicy.ELAPSED_DEADLINE_NONE,
                Long.MAX_VALUE, 1_000L, 5_000L)
                == AppLockAttemptPolicy.ELAPSED_DEADLINE_NONE,
                "initialized no-deadline state never re-reads wall time");

        System.out.println("AppLockAttemptPolicy tests: PASS");
    }
}
