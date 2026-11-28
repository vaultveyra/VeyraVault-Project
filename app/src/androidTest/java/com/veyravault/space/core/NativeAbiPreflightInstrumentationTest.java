package com.veyravault.space.core;

import android.content.Context;

import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.ext.junit.runners.AndroidJUnit4;

import org.junit.Test;
import org.junit.runner.RunWith;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

/** Read-only smoke tests for PackageManager/APK inspection in the instrumentation APK. */
@RunWith(AndroidJUnit4.class)
public final class NativeAbiPreflightInstrumentationTest {

    @Test
    public void instrumentationHarnessApkIsReadAsPureJavaAndSnapshotRemainsBoundToPackage() {
        // Inspect the separate Android test APK, not the Debug target APK. The target
        // intentionally contains an x86_64-only test Probe so it can install on the
        // x86_64 emulator; that Probe must not make the test APK appear non-Java.
        Context context = InstrumentationRegistry.getInstrumentation().getContext();

        NativeAbiPreflight.Result result =
                NativeAbiPreflight.inspectInstalledPackage(context, context.getPackageName());

        assertNotNull("Preflight must always return a result", result);
        assertEquals("The instrumentation APK should remain pure Java",
                NativeAbiPolicy.Decision.ALLOW_PURE_JAVA, result.getDecision());
        assertTrue("A readable unchanged instrumentation APK should pass its file-stamp check",
                result.matchesInstalledPackage(context, context.getPackageName()));
        assertFalse("A preflight result must not be reusable for a different package",
                result.matchesInstalledPackage(context, context.getPackageName() + ".different"));
    }

    @Test
    public void missingPackageMetadataFailsClosedWithoutEngineOrCloneMutation() {
        Context context = InstrumentationRegistry.getInstrumentation().getContext();

        NativeAbiPreflight.Result result = NativeAbiPreflight.inspectInstalledPackage(
                context, "com.veyravault.test.package.that.does.not.exist");

        assertNotNull(result);
        assertEquals(NativeAbiPolicy.Decision.UNKNOWN_APK_METADATA, result.getDecision());
        assertFalse(result.isAllowed());
    }
}
