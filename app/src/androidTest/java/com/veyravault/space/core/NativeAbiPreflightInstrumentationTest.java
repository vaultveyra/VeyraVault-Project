package com.veyravault.space.core;

import android.content.Context;

import androidx.test.core.app.ApplicationProvider;
import androidx.test.ext.junit.runners.AndroidJUnit4;

import org.junit.Test;
import org.junit.runner.RunWith;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

/** Read-only smoke tests for PackageManager/APK inspection in the debug test APK. */
@RunWith(AndroidJUnit4.class)
public final class NativeAbiPreflightInstrumentationTest {

    @Test
    public void debugHarnessApkIsReadAsPureJavaAndSnapshotRemainsBoundToPackage() {
        Context context = ApplicationProvider.getApplicationContext();

        NativeAbiPreflight.Result result =
                NativeAbiPreflight.inspectInstalledPackage(context, context.getPackageName());

        assertNotNull("Preflight must always return a result", result);
        assertEquals("The debug harness excludes native libraries and should be pure Java",
                NativeAbiPolicy.Decision.ALLOW_PURE_JAVA, result.getDecision());
        assertTrue("A readable unchanged debug APK should pass its own file-stamp check",
                result.matchesInstalledPackage(context, context.getPackageName()));
        assertFalse("A preflight result must not be reusable for a different package",
                result.matchesInstalledPackage(context, context.getPackageName() + ".different"));
    }

    @Test
    public void missingPackageMetadataFailsClosedWithoutEngineOrCloneMutation() {
        Context context = ApplicationProvider.getApplicationContext();

        NativeAbiPreflight.Result result = NativeAbiPreflight.inspectInstalledPackage(
                context, "com.veyravault.test.package.that.does.not.exist");

        assertNotNull(result);
        assertEquals(NativeAbiPolicy.Decision.UNKNOWN_APK_METADATA, result.getDecision());
        assertFalse(result.isAllowed());
    }
}
