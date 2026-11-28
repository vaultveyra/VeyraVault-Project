package com.veyravault.space.ui;

import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.widget.CheckBox;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import com.veyravault.space.R;
import com.veyravault.space.core.CloneStore;
import com.veyravault.space.core.LocaleHelper;

public class PermissionsActivity extends BaseActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        boolean fa = LocaleHelper.isPersian(this);
        String pkg = getIntent().getStringExtra("pkg");
        int uid = getIntent().getIntExtra("uid", 0);
        final CloneStore.CloneEntry entry = CloneStore.getClone(this, pkg, uid);

        ScrollView sv = new ScrollView(this);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(40, 40, 40, 40);
        sv.addView(root);

        TextView title = new TextView(this);
        title.setTextSize(19f);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setTextColor(UiPalette.textPrimary(getApplicationContext()));
        title.setText((fa ? "مدیریت مجوزهای کلون: " : "Permissions: ")
                + (entry != null ? entry.displayName : pkg));
        root.addView(title);

        TextView notice = new TextView(this);
        notice.setText(getString(R.string.permission_policy_notice));
        notice.setTextSize(13f);
        notice.setTextColor(UiPalette.warning(getApplicationContext()));
        notice.setPadding(0, 16, 0, 20);
        root.addView(notice);

        if (entry != null) {
            try {
                PackageInfo pi = getPackageManager().getPackageInfo(pkg, PackageManager.GET_PERMISSIONS);
                if (pi.requestedPermissions != null) {
                    for (final String perm : pi.requestedPermissions) {
                        CheckBox cb = new CheckBox(this);
                        cb.setText(perm.replace("android.permission.", ""));
                        // Preserve and display existing local flags, but do not imply
                        // they revoke Android permissions or affect the clone runtime.
                        cb.setChecked(!entry.deniedPermissions.contains(perm));
                        cb.setEnabled(false);
                        root.addView(cb);
                    }
                }
            } catch (Exception ignored) {
                TextView unavailable = new TextView(this);
                unavailable.setText(fa ? "فهرست مجوزهای این برنامه در دسترس نیست."
                        : "The requested-permission list is unavailable.");
                root.addView(unavailable);
            }
        }
        setContentView(sv);
    }
}
