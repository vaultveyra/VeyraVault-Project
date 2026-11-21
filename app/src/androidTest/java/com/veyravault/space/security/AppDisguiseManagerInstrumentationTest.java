package com.veyravault.space.security;

import android.content.ComponentName;
import android.content.Context;
import android.content.pm.PackageManager;

import androidx.test.core.app.ApplicationProvider;
import androidx.test.ext.junit.runners.AndroidJUnit4;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;

import static org.junit.Assert.*;

@RunWith(AndroidJUnit4.class)
public class AppDisguiseManagerInstrumentationTest {
    private Context context;
    private PackageManager packageManager;
    private int[] originalStates;

    @Before
    public void setUp() {
        context = ApplicationProvider.getApplicationContext();
        packageManager = context.getPackageManager();
        originalStates = new int[AppDisguiseManager.ALIASES.length];
        for (int i = 0; i < AppDisguiseManager.ALIASES.length; i++) {
            originalStates[i] = state(i);
        }
    }

    @After
    public void tearDown() {
        for (int i = 0; i < AppDisguiseManager.ALIASES.length; i++) {
            packageManager.setComponentEnabledSetting(
                    component(i), originalStates[i], PackageManager.DONT_KILL_APP);
        }
        for (int i = 0; i < AppDisguiseManager.ALIASES.length; i++) {
            assertEquals("Launcher alias state was not restored for index " + i,
                    originalStates[i], state(i));
        }
    }

    @Test
    public void everyBundledAliasCanBeSelectedAndVerified() {
        for (int target = 0; target < AppDisguiseManager.ALIASES.length; target++) {
            assertTrue("Could not apply launcher alias " + target,
                    AppDisguiseManager.applyDisguise(context, target));
            assertEquals(target, AppDisguiseManager.getActiveDisguiseIndex(context));
            assertExactlyOneAliasEnabled(target);
        }
    }

    @Test
    public void invalidTargetsAreRejectedWithoutChangingComponentStates() {
        int[] before = snapshot();
        assertFalse(AppDisguiseManager.applyDisguise(context, -1));
        assertFalse(AppDisguiseManager.applyDisguise(context, AppDisguiseManager.ALIASES.length));
        assertArrayEquals(before, snapshot());
    }

    @Test
    public void ambiguousAliasConfigurationIsDetectedAndCanBeRepaired() {
        for (int i = 0; i < AppDisguiseManager.ALIASES.length; i++) {
            packageManager.setComponentEnabledSetting(
                    component(i), PackageManager.COMPONENT_ENABLED_STATE_DISABLED,
                    PackageManager.DONT_KILL_APP);
        }
        packageManager.setComponentEnabledSetting(
                component(0), PackageManager.COMPONENT_ENABLED_STATE_ENABLED,
                PackageManager.DONT_KILL_APP);
        packageManager.setComponentEnabledSetting(
                component(2), PackageManager.COMPONENT_ENABLED_STATE_ENABLED,
                PackageManager.DONT_KILL_APP);

        assertEquals(-1, AppDisguiseManager.getActiveDisguiseIndex(context));
        assertTrue(AppDisguiseManager.applyDisguise(context, 4));
        assertEquals(4, AppDisguiseManager.getActiveDisguiseIndex(context));
        assertExactlyOneAliasEnabled(4);
    }

    private void assertExactlyOneAliasEnabled(int expectedIndex) {
        int enabledCount = 0;
        for (int i = 0; i < AppDisguiseManager.ALIASES.length; i++) {
            int componentState = state(i);
            boolean effectivelyEnabled =
                    componentState == PackageManager.COMPONENT_ENABLED_STATE_ENABLED
                    || (componentState == PackageManager.COMPONENT_ENABLED_STATE_DEFAULT && i == 0);
            if (effectivelyEnabled) enabledCount++;
            assertEquals("Unexpected launcher alias state at index " + i,
                    i == expectedIndex, effectivelyEnabled);
        }
        assertEquals(1, enabledCount);
    }

    private int[] snapshot() {
        int[] result = new int[AppDisguiseManager.ALIASES.length];
        for (int i = 0; i < result.length; i++) result[i] = state(i);
        return result;
    }

    private int state(int index) {
        return packageManager.getComponentEnabledSetting(component(index));
    }

    private ComponentName component(int index) {
        return new ComponentName(context, AppDisguiseManager.ALIASES[index]);
    }
}
