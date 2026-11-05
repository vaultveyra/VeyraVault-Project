package com.veyravault.space.ui;

import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.CompoundButton;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import com.veyravault.space.R;
import com.veyravault.space.core.LocaleHelper;
import com.veyravault.space.security.AppDisguiseManager;
import com.veyravault.space.security.SecurityManager;
import com.veyravault.space.security.VaultDeviceAdminReceiver;

public class SecuritySettingsActivity extends BaseActivity {

    private CheckBox antiUninstallSwitch;
    private boolean fa;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        fa = LocaleHelper.isPersian(this);

        ScrollView sv = new ScrollView(this);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(40, 40, 40, 60);
        sv.addView(root);

        TextView title = new TextView(this);
        title.setText(fa ? "مرکز امنیت، تغییر آیکون و محافظت از حذف" : "Security, App Disguise & Anti-Uninstall");
        title.setTextSize(20f);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setTextColor(Color.parseColor("#111827"));
        root.addView(title);

        LinearLayout cardAnti = makeCard();
        TextView antiTitle = new TextView(this);
        antiTitle.setText("🛡️ " + getString(R.string.anti_uninstall_title));
        antiTitle.setTypeface(Typeface.DEFAULT_BOLD);
        antiTitle.setTextSize(16f);
        cardAnti.addView(antiTitle);

        TextView antiDesc = new TextView(this);
        antiDesc.setText(getString(R.string.anti_uninstall_desc));
        antiDesc.setTextSize(13f);
        antiDesc.setTextColor(Color.parseColor("#4B5563"));
        antiDesc.setPadding(0, 10, 0, 16);
        cardAnti.addView(antiDesc);

        antiUninstallSwitch = new CheckBox(this);
        antiUninstallSwitch.setText(fa ? "قفل کردن حذف برنامه (غیرقابل حذف شدن)" : "Prevent App Uninstall (Active Protection)");
        antiUninstallSwitch.setChecked(VaultDeviceAdminReceiver.isAntiUninstallActive(this));
        antiUninstallSwitch.setOnCheckedChangeListener(new CompoundButton.OnCheckedChangeListener() {
            @Override
            public void onCheckedChanged(CompoundButton buttonView, boolean isChecked) {
                VaultDeviceAdminReceiver.setAntiUninstallEnabled(SecuritySettingsActivity.this, isChecked, 901);
                if (!isChecked) {
                    Toast.makeText(SecuritySettingsActivity.this,
                            fa ? "محافظت حذف غیرفعال شد. اکنون برنامه قابل حذف است." : "Uninstall protection disabled.",
                            Toast.LENGTH_SHORT).show();
                }
            }
        });
        cardAnti.addView(antiUninstallSwitch);
        root.addView(cardAnti);

        LinearLayout cardLock = makeCard();
        TextView lockTitle = new TextView(this);
        lockTitle.setText(fa ? "🔒 قفل امنیتی برنامه (الگو یا پین)" : "🔒 App Lock (Pattern or PIN)");
        lockTitle.setTypeface(Typeface.DEFAULT_BOLD);
        lockTitle.setTextSize(16f);
        cardLock.addView(lockTitle);

        Button btnPattern = new Button(this);
        btnPattern.setAllCaps(false);
        btnPattern.setText(fa ? "تنظیم قفل الگو (Pattern Lock)" : "Set Pattern Lock");
        btnPattern.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Intent i = new Intent(SecuritySettingsActivity.this, SecurityLockActivity.class);
                i.putExtra("setup_mode", SecurityManager.MODE_PATTERN);
                startActivity(i);
            }
        });
        cardLock.addView(btnPattern);

        Button btnPin = new Button(this);
        btnPin.setAllCaps(false);
        btnPin.setText(fa ? "تنظیم رمز پین عددی (PIN Code)" : "Set Numeric PIN Lock");
        btnPin.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Intent i = new Intent(SecuritySettingsActivity.this, SecurityLockActivity.class);
                i.putExtra("setup_mode", SecurityManager.MODE_PIN);
                startActivity(i);
            }
        });
        cardLock.addView(btnPin);

        Button btnDisableLock = new Button(this);
        btnDisableLock.setAllCaps(false);
        btnDisableLock.setText(fa ? "غیرفعال کردن قفل برنامه" : "Disable App Lock");
        btnDisableLock.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                SecurityManager.setLockCredential(SecuritySettingsActivity.this, SecurityManager.MODE_NONE, "");
                Toast.makeText(SecuritySettingsActivity.this, fa ? "قفل برنامه غیرفعال شد" : "App lock disabled", Toast.LENGTH_SHORT).show();
            }
        });
        cardLock.addView(btnDisableLock);
        root.addView(cardLock);

        LinearLayout cardDisguise = makeCard();
        TextView disTitle = new TextView(this);
        disTitle.setText(fa ? "🎭 تغییر آیکون و نام برنامه در صفحه گوشی" : "🎭 Change App Icon & Name (Disguise)");
        disTitle.setTypeface(Typeface.DEFAULT_BOLD);
        disTitle.setTextSize(16f);
        cardDisguise.addView(disTitle);

        String[] disguiseLabels = {
            fa ? "۱. پیش‌فرض (VeyraVault)" : "1. Default (VeyraVault)",
            fa ? "۲. ماشین‌حساب (Calculator)" : "2. Calculator",
            fa ? "۳. تقویم (Calendar)" : "3. Calendar",
            fa ? "۴. یادداشت‌ها (Notes)" : "4. Notes",
            fa ? "۵. آب‌وهوا (Weather)" : "5. Weather"
        };

        for (int i = 0; i < disguiseLabels.length; i++) {
            final int idx = i;
            Button b = new Button(this);
            b.setAllCaps(false);
            b.setText(disguiseLabels[i]);
            b.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    AppDisguiseManager.applyDisguise(SecuritySettingsActivity.this, idx);
                    Toast.makeText(SecuritySettingsActivity.this,
                            fa ? "آیکون و نام برنامه تغییر کرد!" : "App icon and name updated!",
                            Toast.LENGTH_LONG).show();
                }
            });
            cardDisguise.addView(b);
        }
        root.addView(cardDisguise);

        setContentView(sv);
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (antiUninstallSwitch != null) {
            antiUninstallSwitch.setChecked(VaultDeviceAdminReceiver.isAntiUninstallActive(this));
        }
    }

    private LinearLayout makeCard() {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setBackgroundResource(R.drawable.bg_card_rounded);
        card.setPadding(36, 32, 36, 32);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        lp.topMargin = 28;
        card.setLayoutParams(lp);
        return card;
    }
}
