package com.veyravault.space.security;

import android.app.Activity;
import android.app.admin.DeviceAdminReceiver;
import android.app.admin.DevicePolicyManager;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import com.veyravault.space.core.LocaleHelper;

public class VaultDeviceAdminReceiver extends DeviceAdminReceiver {

    public static ComponentName getComponentName(Context ctx) {
        return new ComponentName(ctx.getApplicationContext(), VaultDeviceAdminReceiver.class);
    }

    public static boolean isAntiUninstallActive(Context ctx) {
        DevicePolicyManager dpm = (DevicePolicyManager) ctx.getSystemService(Context.DEVICE_POLICY_SERVICE);
        return dpm != null && dpm.isAdminActive(getComponentName(ctx));
    }

    public static void setAntiUninstallEnabled(Activity act, boolean enable, int reqCode) {
        DevicePolicyManager dpm = (DevicePolicyManager) act.getSystemService(Context.DEVICE_POLICY_SERVICE);
        ComponentName comp = getComponentName(act);
        if (dpm == null) return;
        if (enable && !dpm.isAdminActive(comp)) {
            Intent intent = new Intent(DevicePolicyManager.ACTION_ADD_DEVICE_ADMIN);
            intent.putExtra(DevicePolicyManager.EXTRA_DEVICE_ADMIN, comp);
            intent.putExtra(DevicePolicyManager.EXTRA_ADD_EXPLANATION,
                    LocaleHelper.isPersian(act)
                            ? "این گزینه دسترسی مدیر دستگاه اندروید را فعال می‌کند. برای حذف VeyraVault ابتدا باید این دسترسی را از تنظیمات سیستم غیرفعال کنید. این قابلیت برنامه را غیرقابل‌حذف نمی‌کند و مدیر دستگاه نیز از تنظیمات اندروید قابل لغو است."
                            : "This activates Android Device Admin. To uninstall VeyraVault, first deactivate its admin access in Android Settings. This does not make the app impossible to uninstall, and admin access can be revoked in system settings.");
            act.startActivityForResult(intent, reqCode);
        } else if (!enable && dpm.isAdminActive(comp)) {
            dpm.removeActiveAdmin(comp);
        }
    }
}
