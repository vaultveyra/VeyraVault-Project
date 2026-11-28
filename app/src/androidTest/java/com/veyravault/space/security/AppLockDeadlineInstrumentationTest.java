package com.veyravault.space.security;

import androidx.test.ext.junit.runners.AndroidJUnit4;

import org.junit.Test;
import org.junit.runner.RunWith;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

@RunWith(AndroidJUnit4.class)
public class AppLockDeadlineInstrumentationTest {
    @Test
    public void allSupportedTimeoutsMapToExpectedDurations() {
        assertEquals(250L, AppLockDeadline.timeoutMillis(AppLockDeadline.TIMEOUT_IMMEDIATELY_SECONDS));
        assertEquals(30_000L, AppLockDeadline.timeoutMillis(AppLockDeadline.TIMEOUT_30_SECONDS));
        assertEquals(60_000L, AppLockDeadline.timeoutMillis(AppLockDeadline.TIMEOUT_1_MINUTE));
        assertEquals(300_000L, AppLockDeadline.timeoutMillis(AppLockDeadline.TIMEOUT_5_MINUTES));
    }

    @Test
    public void deadlineBoundaryIsInclusiveAndUsesElapsedTime() {
        long deadline = AppLockDeadline.deadlineAfter(12_000L, AppLockDeadline.TIMEOUT_30_SECONDS);
        assertEquals(42_000L, deadline);
        assertFalse(AppLockDeadline.isExpired(deadline, 41_999L));
        assertTrue(AppLockDeadline.isExpired(deadline, 42_000L));
        assertTrue(AppLockDeadline.isExpired(deadline, 90_000L));
        assertEquals(0L, AppLockDeadline.remainingMillis(deadline, 90_000L));
    }

    @Test
    public void invalidTimeoutFailsClosedAndMissingDeadlineIsDistinct() {
        assertEquals(250L, AppLockDeadline.timeoutMillis(-1));
        assertEquals(250L, AppLockDeadline.timeoutMillis(17));
        assertEquals(-1L, AppLockDeadline.remainingMillis(-1L, 5_000L));
        assertFalse(AppLockDeadline.isExpired(-1L, 5_000L));
    }

    @Test
    public void deadlineAdditionSaturatesAtLongMaximum() {
        assertEquals(Long.MAX_VALUE,
                AppLockDeadline.deadlineAfter(Long.MAX_VALUE - 10L, AppLockDeadline.TIMEOUT_30_SECONDS));
    }
}
