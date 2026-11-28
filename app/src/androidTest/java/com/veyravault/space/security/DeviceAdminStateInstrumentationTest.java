package com.veyravault.space.security;

import android.app.admin.DevicePolicyManager;
import android.content.ComponentName;
import android.content.Context;

import androidx.test.core.app.ApplicationProvider;
import androidx.test.ext.junit.runners.AndroidJUnit4;

import org.junit.Test;
import org.junit.runner.RunWith;

import static org.junit.Assert.*;

@RunWith(AndroidJUnit4.class)
public class DeviceAdminStateInstrumentationTest {
    @Test
    public void reportedAdminStateMatchesAndroidDevicePolicyManager() {
        Context context = ApplicationProvider.getApplicationContext();
        DevicePolicyManager manager = (DevicePolicyManager)
                context.getSystemService(Context.DEVICE_POLICY_SERVICE);
        assertNotNull("DevicePolicyManager service must be available", manager);

        ComponentName receiver = VaultDeviceAdminReceiver.getComponentName(context);
        assertNotNull(receiver);
        boolean systemReportedState = manager.isAdminActive(receiver);

        // Read-only assertion: this test never requests or revokes Device Admin.
        assertEquals(systemReportedState,
                VaultDeviceAdminReceiver.isAntiUninstallActive(context));
    }
}
