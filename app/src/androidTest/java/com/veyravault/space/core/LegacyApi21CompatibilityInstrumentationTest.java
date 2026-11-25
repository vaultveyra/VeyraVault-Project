package com.veyravault.space.core;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import android.content.Context;
import android.os.Build;

import androidx.test.core.app.ApplicationProvider;
import androidx.test.ext.junit.runners.AndroidJUnit4;

import org.junit.Test;
import org.junit.runner.RunWith;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.URL;
import java.util.Enumeration;

/** Runtime smoke tests executed on the declared minimum Android API level. */
@RunWith(AndroidJUnit4.class)
public class LegacyApi21CompatibilityInstrumentationTest {

    @Test
    public void minimumSdkPackageManagerAndAbiPreflightWorkOnApi21() throws Exception {
        assertEquals("This test must run on Android API 21", 21, Build.VERSION.SDK_INT);
        Context context = ApplicationProvider.getApplicationContext();
        assertTrue(context.getPackageManager().getApplicationInfo(
                context.getPackageName(), 0) != null);

        // Exercises the API-21 PackageManager overload, splitSourceDirs access, APK ZIP
        // scanning, and the legacy host-bitness fallback (without calling API 23/33 methods).
        NativeAbiPreflight.Result result = NativeAbiPreflight.inspectInstalledPackage(
                context, context.getPackageName());
        assertTrue(result.getDiagnosticCode(), result.isAllowed());
        assertTrue("Package fingerprint must still match immediately after preflight",
                result.matchesInstalledPackage(context, context.getPackageName()));
    }

    @Test
    public void javaCalendarAndLegacyDateConversionWorkOnApi21() {
        String tehran = DashboardDateFormatter.formatTehranJalaliDate(0L, false);
        String newYork = DashboardDateFormatter.formatNewYorkGregorianDate(0L, false);
        assertFalse(tehran.trim().isEmpty());
        assertFalse(newYork.trim().isEmpty());
    }

    @Test
    public void coroutineServiceDescriptorsRemainDiscoverableOnApi21() throws Exception {
        Context context = ApplicationProvider.getApplicationContext();
        ClassLoader loader = context.getClassLoader();
        assertServiceProvider(loader,
                "kotlinx.coroutines.internal.MainDispatcherFactory",
                "kotlinx.coroutines.android.AndroidDispatcherFactory");
        assertServiceProvider(loader,
                "kotlinx.coroutines.CoroutineExceptionHandler",
                "kotlinx.coroutines.android.AndroidExceptionPreHandler");
    }

    private static void assertServiceProvider(
            ClassLoader loader, String serviceName, String expectedProvider) throws Exception {
        String resourceName = "META-INF/services/" + serviceName;
        Enumeration<URL> resources = loader.getResources(resourceName);
        boolean resourceFound = false;
        boolean providerFound = false;
        while (resources.hasMoreElements()) {
            resourceFound = true;
            URL resource = resources.nextElement();
            try (InputStream input = resource.openStream();
                 BufferedReader reader = new BufferedReader(new InputStreamReader(input, "UTF-8"))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    String provider = line.split("#", 2)[0].trim();
                    if (expectedProvider.equals(provider)) providerFound = true;
                }
            }
        }
        assertTrue("Missing runtime service resource: " + resourceName, resourceFound);
        assertTrue("Missing provider " + expectedProvider + " in " + resourceName, providerFound);
        assertTrue("Provider class must be loadable: " + expectedProvider,
                Class.forName(expectedProvider, false, loader) != null);
    }
}
