package com.veyravault.space.core;

import androidx.test.ext.junit.runners.AndroidJUnit4;

import org.junit.Test;
import org.junit.runner.RunWith;

import static org.junit.Assert.assertEquals;

/** Pure policy tests; these cases never load the native Engine or touch Clone state. */
@RunWith(AndroidJUnit4.class)
public final class NativeNeonPolicyInstrumentationTest {

    @Test
    public void arm64HostAbiIsAcceptedWithoutOptionalArmv7Probe() {
        assertEquals(NativeAbiPolicy.Decision.ALLOW_ARM64,
                NativeAbiPolicy.evaluateHostCpu("arm64-v8a",
                        NativeNeonProbe.UNKNOWN).getDecision());
    }

    @Test
    public void armv7RequiresPositiveRuntimeNeonDetection() {
        assertEquals(NativeAbiPolicy.Decision.ALLOW_ARM32,
                NativeAbiPolicy.evaluateHostCpu("armeabi-v7a",
                        NativeNeonProbe.SUPPORTED).getDecision());
    }

    @Test
    public void armv7WithoutNeonIsRejected() {
        assertEquals(NativeAbiPolicy.Decision.REJECT_ARMV7_NEON_UNSUPPORTED,
                NativeAbiPolicy.evaluateHostCpu("armeabi-v7a",
                        NativeNeonProbe.UNSUPPORTED).getDecision());
    }

    @Test
    public void unknownArmv7CapabilityFailsClosed() {
        assertEquals(NativeAbiPolicy.Decision.UNKNOWN_ARMV7_NEON_CAPABILITY,
                NativeAbiPolicy.evaluateHostCpu("armeabi-v7a",
                        NativeNeonProbe.UNKNOWN).getDecision());
    }

    @Test
    public void unsupportedHostAbiIsRejected() {
        assertEquals(NativeAbiPolicy.Decision.REJECT_UNSUPPORTED_ENGINE_HOST_ABI,
                NativeAbiPolicy.evaluateHostCpu("x86_64",
                        NativeNeonProbe.UNKNOWN).getDecision());
    }

    @Test
    public void genericArmeabiIsRejectedBecauseReleaseDoesNotPackageIt() {
        assertEquals(NativeAbiPolicy.Decision.REJECT_UNSUPPORTED_ENGINE_HOST_ABI,
                NativeAbiPolicy.evaluateHostCpu("armeabi",
                        NativeNeonProbe.SUPPORTED).getDecision());
    }
}
