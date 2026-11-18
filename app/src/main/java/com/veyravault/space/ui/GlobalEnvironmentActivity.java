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
import com.veyravault.space.core.AsyncCloneRepository;
import com.veyravault.space.core.CloneStore;
import com.veyravault.space.core.LocaleHelper;
import com.veyravault.space.core.VirtualHookManager;

public class GlobalEnvironmentActivity extends BaseActivity {
    private AsyncCloneRepository repository;
    private boolean fa;
    private boolean profileLoaded;
    private boolean masterGpsLoaded;
    private boolean loadFailed;
    private CloneStore.GlobalEnvConfig config;
    private CheckBox enableGlobal;
    private EditText brandEt;
    private EditText modelEt;
    private EditText countryEt;
    private EditText simOpEt;
    private CheckBox masterGps;
    private Button saveButton;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        fa = LocaleHelper.isPersian(this);
        repository = AsyncCloneRepository.getInstance(getApplicationContext());
        config = new CloneStore.GlobalEnvConfig();
        buildContent();
        setContentView(contentView);
        setControlsEnabled(false);
        loadSettings();
    }


    private void buildContent() {
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

        enableGlobal = new CheckBox(this);
        enableGlobal.setText(fa ? "ذخیره پروفایل سراسری دستگاه (فقط اطلاعات)" : "Save Global Device Profile (Metadata Only)");
        enableGlobal.setChecked(config.enabled);
        root.addView(enableGlobal);

        brandEt = new EditText(this);
        brandEt.setHint("Brand (e.g. samsung)");
        brandEt.setText(config.brand);
        root.addView(brandEt);

        modelEt = new EditText(this);
        modelEt.setHint("Model (e.g. SM-S928B)");
        modelEt.setText(config.model);
        root.addView(modelEt);

        countryEt = new EditText(this);
        countryEt.setHint("Country ISO (us, de, ae, tr, gb)");
        countryEt.setText(config.countryIso);
        root.addView(countryEt);

        simOpEt = new EditText(this);
        simOpEt.setHint("SIM MCC/MNC (e.g. 310260 for US T-Mobile)");
        simOpEt.setText(config.simOperator);
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
        for (final String[] preset : presets) {
            Button button = new Button(this);
            button.setAllCaps(false);
            button.setText(preset[0]);
            button.setOnClickListener(v -> {
                brandEt.setText(preset[1]);
                modelEt.setText(preset[2]);
                countryEt.setText(preset[3]);
                simOpEt.setText(preset[4]);
            });
            root.addView(button);
        }

        masterGps = new CheckBox(this);
        masterGps.setText(fa ? "کلید اصلی فعال‌سازی موقعیت مکانی مجازی (Master Mock GPS)" : "Master Mock GPS Switch");
        masterGps.setPadding(0, 24, 0, 24);
        root.addView(masterGps);

        saveButton = new Button(this);
        saveButton.setBackgroundResource(R.drawable.bg_pill_blue);
        saveButton.setTextColor(Color.WHITE);
        saveButton.setText(fa ? "ذخیره پروفایل و همگام‌سازی موقعیت کلون‌ها" : "Save Profile & Sync Clone Locations");
        saveButton.setOnClickListener(v -> saveSettings());
        root.addView(saveButton, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        contentView = sv;
    }

    private View contentView;

    private void setControlsEnabled(boolean enabled) {
        if (saveButton != null) saveButton.setEnabled(enabled && !loadFailed);
        if (enableGlobal != null) enableGlobal.setEnabled(enabled);
        if (brandEt != null) brandEt.setEnabled(enabled);
        if (modelEt != null) modelEt.setEnabled(enabled);
        if (countryEt != null) countryEt.setEnabled(enabled);
        if (simOpEt != null) simOpEt.setEnabled(enabled);
        if (masterGps != null) masterGps.setEnabled(enabled);
    }

    private void loadSettings() {
        repository.loadGlobalEnvironment(result -> {
            if (isFinishing() || isDestroyed()) return;
            if (!result.isSuccess()) {
                failLoading((fa ? "خواندن پروفایل ناموفق بود: " : "Could not read global profile: ") + result.getMessage());
                return;
            }
            config = result.getValue();
            enableGlobal.setChecked(config.enabled);
            brandEt.setText(config.brand);
            modelEt.setText(config.model);
            countryEt.setText(config.countryIso);
            simOpEt.setText(config.simOperator);
            profileLoaded = true;
            finishLoadingIfReady();
        });
        repository.loadMasterMockGpsEnabled(result -> {
            if (isFinishing() || isDestroyed()) return;
            if (!result.isSuccess()) {
                failLoading((fa ? "خواندن وضعیت Master GPS ناموفق بود: " : "Could not read Master GPS: ") + result.getMessage());
                return;
            }
            masterGps.setChecked(Boolean.TRUE.equals(result.getValue()));
            masterGpsLoaded = true;
            finishLoadingIfReady();
        });
    }

    private void finishLoadingIfReady() {
        if (profileLoaded && masterGpsLoaded && !loadFailed) setControlsEnabled(true);
    }

    private void failLoading(String message) {
        loadFailed = true;
        setControlsEnabled(false);
        if (!isFinishing() && !isDestroyed())
            Toast.makeText(this, message, Toast.LENGTH_LONG).show();
    }

    private void saveSettings() {
        if (!profileLoaded || !masterGpsLoaded || loadFailed) return;
        saveButton.setEnabled(false);
        final CloneStore.GlobalEnvConfig updated = new CloneStore.GlobalEnvConfig();
        updated.enabled = enableGlobal.isChecked();
        updated.brand = brandEt.getText().toString().trim();
        updated.manufacturer = updated.brand;
        updated.model = modelEt.getText().toString().trim();
        updated.device = config.device;
        updated.countryIso = countryEt.getText().toString().trim().toLowerCase(java.util.Locale.ROOT);
        updated.simOperator = simOpEt.getText().toString().trim();
        updated.simOperatorName = config.simOperatorName;
        final boolean masterGpsEnabled = masterGps.isChecked();

        repository.saveGlobalEnvironment(updated, profileResult -> {
            if (isFinishing() || isDestroyed()) return;
            if (!profileResult.isSuccess()) {
                saveButton.setEnabled(true);
                showSaveFailure((fa ? "پروفایل ذخیره نشد: " : "Profile was not saved: ")
                        + profileResult.getMessage());
                return;
            }
            repository.setMasterMockGpsEnabled(masterGpsEnabled, gpsResult -> {
                if (isFinishing() || isDestroyed()) return;
                if (!gpsResult.isSuccess()) {
                    saveButton.setEnabled(true);
                    showSaveFailure(fa
                            ? "پروفایل ذخیره شد، اما Master GPS ذخیره نشد. همگام‌سازی اجرا نشد: " + gpsResult.getMessage()
                            : "Profile was saved, but Master GPS was not. Hook synchronization was not run: "
                                    + gpsResult.getMessage());
                    return;
                }
                // Both independent commits are confirmed before requesting hook synchronization.
                VirtualHookManager.syncAllHooks(getApplicationContext());
                Toast.makeText(this, fa
                        ? "پروفایل و Master GPS ذخیره شدند؛ همگام‌سازی موقعیت کلون‌ها درخواست شد. مشخصات دستگاه/سیم‌کارت فقط اطلاعات هستند."
                        : "Profile and Master GPS were saved; clone location hook sync was requested. Device/SIM values are metadata only and are not applied to clones.",
                        Toast.LENGTH_LONG).show();
                finish();
            });
        });
    }

    private void showSaveFailure(String message) {
        if (!isFinishing() && !isDestroyed())
            Toast.makeText(this, message, Toast.LENGTH_LONG).show();
    }
}
