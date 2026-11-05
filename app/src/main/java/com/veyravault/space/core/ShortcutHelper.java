package com.veyravault.space.core;

import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ShortcutInfo;
import android.content.pm.ShortcutManager;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.drawable.Drawable;
import android.graphics.drawable.Icon;
import android.os.Build;
import android.widget.Toast;
import com.veyravault.space.ui.MainActivity;

public class ShortcutHelper {
    public static void addCloneToHome(Context ctx, CloneStore.CloneEntry entry) {
        Intent launchIntent = new Intent(ctx, MainActivity.class);
        launchIntent.setAction(Intent.ACTION_VIEW);
        launchIntent.putExtra("shortcut_pkg", entry.packageName);
        launchIntent.putExtra("shortcut_uid", entry.userId);
        launchIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);

        Bitmap bmp = getAppBitmap(ctx, entry.packageName);
        String label = entry.displayName + " (" + entry.getSpaceNumber() + ")";

        if (Build.VERSION.SDK_INT >= 26) {
            ShortcutManager sm = ctx.getSystemService(ShortcutManager.class);
            if (sm != null && sm.isRequestPinShortcutSupported()) {
                ShortcutInfo info = new ShortcutInfo.Builder(ctx, entry.packageName + "_" + entry.userId)
                        .setShortLabel(label)
                        .setIcon(Icon.createWithBitmap(bmp))
                        .setIntent(launchIntent)
                        .build();
                PendingIntent cb = PendingIntent.getBroadcast(ctx, 0, new Intent(), PendingIntent.FLAG_IMMUTABLE);
                sm.requestPinShortcut(info, cb.getIntentSender());
                return;
            }
        }
        Intent legacy = new Intent("com.android.launcher.action.INSTALL_SHORTCUT");
        legacy.putExtra(Intent.EXTRA_SHORTCUT_INTENT, launchIntent);
        legacy.putExtra(Intent.EXTRA_SHORTCUT_NAME, label);
        legacy.putExtra(Intent.EXTRA_SHORTCUT_ICON, bmp);
        ctx.sendBroadcast(legacy);
        Toast.makeText(ctx, LocaleHelper.isPersian(ctx) ? "میانبر به صفحه اصلی اضافه شد" : "Shortcut added to Home", Toast.LENGTH_SHORT).show();
    }

    private static Bitmap getAppBitmap(Context ctx, String pkg) {
        try {
            Drawable d = ctx.getPackageManager().getApplicationIcon(pkg);
            Bitmap b = Bitmap.createBitmap(128, 128, Bitmap.Config.ARGB_8888);
            Canvas c = new Canvas(b);
            d.setBounds(0, 0, 128, 128);
            d.draw(c);
            return b;
        } catch (Exception e) {
            return Bitmap.createBitmap(64, 64, Bitmap.Config.ARGB_8888);
        }
    }
}
