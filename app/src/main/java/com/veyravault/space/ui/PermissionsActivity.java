package com.veyravault.space.ui;

import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.widget.CheckBox;
import android.widget.CompoundButton;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
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
        title.setTextColor(Color.parseColor("#111827"));
        title.setText((fa ? "مدیریت مجوزهای کلون: " : "Permissions: ") + (entry != null ? entry.displayName : pkg));
        root.addView(title);

        if (entry != null) {
            try {
                PackageInfo pi = getPackageManager().getPackageInfo(pkg, PackageManager.GET_PERMISSIONS);
                if (pi.requestedPermissions != null) {
                    for (final String perm : pi.requestedPermissions) {
                        CheckBox cb = new CheckBox(this);
                        cb.setText(perm.replace("android.permission.", ""));
                        cb.setChecked(!entry.deniedPermissions.contains(perm));
                        cb.setOnCheckedChangeListener(new CompoundButton.OnCheckedChangeListener() {
                            @Override
                            public void onCheckedChanged(CompoundButton b, boolean granted) {
                                if (granted) entry.deniedPermissions.remove(perm);
                                else entry.deniedPermissions.add(perm);
                                CloneStore.upsertClone(PermissionsActivity.this, entry);
                            }
                        });
                        root.addView(cb);
                    }
                }
            } catch (Exception ignored) {}
        }
        setContentView(sv);
    }
}
