package com.veyravault.space.core;

import androidx.test.ext.junit.runners.AndroidJUnit4;

import org.junit.Test;
import org.junit.runner.RunWith;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

@RunWith(AndroidJUnit4.class)
public class VirtualHookManagerInstrumentationTest {
    @Test public void locationReadbackIsBoundToExactPackageAndUser() {
        VirtualHookManager.LocationApplyResult unbound =
                new VirtualHookManager.LocationApplyResult(
                        VirtualHookManager.LocationStatus.APPLIED,
                        "OWN_MODE_AND_COORDINATES_READ_BACK",
                        ProfileResolver.Source.CLONE,
                        ProfileResolver.Source.GLOBAL,
                        ProfileResolver.Source.GLOBAL);

        VirtualHookManager.LocationApplyResult cloneA =
                VirtualHookManager.LocationApplyResult.bindToClone(
                        "com.example.clone.alpha", 21, unbound);
        VirtualHookManager.LocationApplyResult cloneB =
                VirtualHookManager.LocationApplyResult.bindToClone(
                        "com.example.clone.beta", 22, unbound);

        assertTrue(cloneA.belongsTo("com.example.clone.alpha", 21));
        assertFalse(cloneA.belongsTo("com.example.clone.beta", 22));
        assertFalse(cloneA.belongsTo("com.example.clone.alpha", 22));
        assertTrue(cloneB.belongsTo("com.example.clone.beta", 22));
        assertFalse(cloneB.belongsTo("com.example.clone.alpha", 21));
        assertEquals(VirtualHookManager.LocationStatus.APPLIED, cloneA.status);
        assertTrue(cloneA.verifiedAt > 0L);
        assertTrue(cloneB.verifiedAt > 0L);
    }
}
