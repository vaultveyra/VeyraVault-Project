package com.veyravault.space.ui;

import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import com.veyravault.space.R;
import com.veyravault.space.core.CloneStore;
import com.veyravault.space.core.LocaleHelper;

public class GlobalEnvironmentActivity extends BaseActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        final boolean fa = LocaleHelper.isPersian(this);
        final CloneStore.GlobalEnvConfig cfg = CloneStore.getGlobalEnv(this);

        ScrollView sv = new ScrollView(this);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(40, 40, 40, 60);
        sv.addView(root);

        TextView title = new TextView(this);
        title.setText(fa ? "پروفایل سراسری دستگاه (اطلاعات ذخیره‌شده)" : "Global Device Profile (Saved Metadata)");
        title.setTextSize(20f);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setTextColor(Color.parseColor("#111827"));
        root.addView(title);

        TextView desc = new TextView(this);
        desc.setTextSize(13f);
        desc.setTextColor(Color.parseColor("#4B5563"));
        desc.setPadding(0, 12, 0, 28);
        desc.setText(fa
                ? "توجه: مدل دستگاه، کشور و اپراتور در این نسخه فقط به‌عنوان اطلاعات پروفایل ذخیره می‌شوند و توسط موتور فعلی روی کلون‌ها اعمال نمی‌شوند. موقعیت مکانی هر کلون جداگانه از طریق API محدود به بسته و کاربر مجازی موتور تنظیم می‌شود. این گزینه محدودیت منطقه‌ای سرویس‌های دیگر را دور نمی‌زند."
                : "Note: device model, country and operator values are saved as profile metadata only. The pinned engine version does not expose a verified package/user-scoped API to apply these values to clones. Clone locations are configured separately through the engine's package- and virtual-user-scoped location API. This setting does not bypass third-party regional restrictions.");
        root.addView(desc);

        final CheckBox enableGlobal = new CheckBox(this);
        enableGlobal.setText(fa ? "ذخیره پروفایل سراسری دستگاه (فقط اطلاعات)" : "Save Global Device Profile (Metadata Only)");
        enableGlobal.setChecked(cfg.enabled);
        root.addView(enableGlobal);

        final EditText brandEt = new EditText(this);
        brandEt.setHint("Brand (e.g. samsung)");
        brandEt.setText(cfg.brand);
        root.addView(brandEt);

        final EditText modelEt = new EditText(this);
        modelEt.setHint("Model (e.g. SM-S928B)");
        modelEt.setText(cfg.model);
        root.addView(modelEt);

        final EditText countryEt = new EditText(this);
        countryEt.setHint("Country ISO (us, de, ae, tr, gb)");
        countryEt.setText(cfg.countryIso);
        root.addView(countryEt);

        final EditText simOpEt = new EditText(this);
        simOpEt.setHint("SIM MCC/MNC (e.g. 310260 for US T-Mobile)");
        simOpEt.setText(cfg.simOperator);
        root.addView(simOpEt);

        TextView presetTitle = new TextView(this);
        presetTitle.setText(fa ? "پروفایل‌های آماده جهانی (با یک لمس انتخاب کنید):" : "One-Tap Global Presets:");
        presetTitle.setTypeface(Typeface.DEFAULT_BOLD);
        presetTitle.setPadding(0, 24, 0, 12);
        root.addView(presetTitle);

        String[][] presets = {
            {"🇺🇸 Samsung Galaxy S24 Ultra (USA / T-Mobile)", "samsung", "SM-S928B", "us", "310260"},
            {"🇩🇪 Google Pixel 8 Pro (Germany / Telekom)", "google", "Pixel 8 Pro", "de", "26201"},
            {"🇦🇪 Samsung Galaxy S23 Ultra (UAE / Etisalat)", "samsung", "SM-S918B", "ae", "42402"},
            {"🇹🇷 Xiaomi 14 Pro (Turkey / Turkcell)", "Xiaomi", "23116PN5BC", "tr", "28601"}
        };
        for (final String[] p : presets) {
            Button b = new Button(this);
            b.setAllCaps(false);
            b.setText(p[0]);
            b.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    brandEt.setText(p[1]);
                    modelEt.setText(p[2]);
                    countryEt.setText(p[3]);
                    simOpEt.setText(p[4]);
                }
            });
            root.addView(b);
        }

        final CheckBox masterGps = new CheckBox(this);
        masterGps.setText(fa ? "کلید اصلی فعال‌سازی موقعیت مکانی مجازی (Master Mock GPS)" : "Master Mock GPS Switch");
        masterGps.setChecked(CloneStore.isMasterMockGpsEnabled(this));
        masterGps.setPadding(0, 24, 0, 24);
        root.addView(masterGps);

        Button saveBtn = new Button(this);
        saveBtn.setBackgroundResource(R.drawable.bg_pill_blue);
        saveBtn.setTextColor(Color.WHITE);
        saveBtn.setText(fa ? "ذخیره پروفایل و همگام‌سازی موقعیت کلون‌ها" : "Save Profile & Sync Clone Locations");
        saveBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                cfg.enabled = enableGlobal.isChecked();
                cfg.brand = brandEt.getText().toString().trim();
                cfg.manufacturer = cfg.brand;
                cfg.model = modelEt.getText().toString().trim();
                cfg.countryIso = countryEt.getText().toString().trim().toLowerCase();
                cfg.simOperator = simOpEt.getText().toString().trim();
                CloneStore.saveGlobalEnv(GlobalEnvironmentActivity.this, cfg);
                CloneStore.setMasterMockGpsEnabled(GlobalEnvironmentActivity.this, masterGps.isChecked());
                CloneStore.syncAllHooks(GlobalEnvironmentActivity.this);
                Toast.makeText(GlobalEnvironmentActivity.this,
                        fa ? "پروفایل ذخیره شد؛ موقعیت کلون‌ها همگام‌سازی شد. مشخصات دستگاه/سیم‌کارت فقط ذخیره شده‌اند و اعمال نمی‌شوند." : "Profile saved and clone locations synced. Device/SIM values are stored only, not applied.",
                        Toast.LENGTH_SHORT).show();
                finish();
            }
        });
        root.addView(saveBtn, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        setContentView(sv);
    }
}
