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
import com.veyravault.space.core.ProfileSettings;

public class GlobalEnvironmentActivity extends BaseActivity {
    private AsyncCloneRepository repository;
    private boolean fa;
    private boolean profileLoaded;
    private boolean locationProfileLoaded;
    private boolean masterGpsLoaded;
    private boolean loadFailed;
    private CloneStore.GlobalEnvConfig config;
    private ProfileSettings globalProfile;
    private CheckBox globalLocationInherit;
    private CheckBox globalLocationEnabled;
    private EditText globalLatitudeEt;
    private EditText globalLongitudeEt;
    private TextView resetGlobalLocationButton;
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
                : "Note: device model, country and operator values are saved as profile metadata only and are not applied to clones. The pinned engine version does not expose a verified package/user-scoped API to apply these values. Clone locations are configured separately through the engine's package- and virtual-user-scoped location API. This setting does not bypass third-party regional restrictions.");
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

        TextView locationTitle = new TextView(this);
        locationTitle.setText(fa ? "پیش‌فرض موقعیت مکانی سراسری" : "Global Location Defaults");
        locationTitle.setTextSize(17f);
        locationTitle.setTypeface(Typeface.DEFAULT_BOLD);
        locationTitle.setPadding(0, 20, 0, 8);
        root.addView(locationTitle);

        TextView locationDesc = new TextView(this);
        locationDesc.setTextSize(13f);
        locationDesc.setTextColor(Color.parseColor("#4B5563"));
        locationDesc.setText(fa
                ? "اولویت هر فیلد: تنظیم اختصاصی کلون، سپس این پروفایل سراسری، سپس مقدار امن سیستم. Master Mock GPS کلید قطع‌کننده اصلی است."
                : "Per-field priority: Clone override, then this Global profile, then the safe system default. Master Mock GPS remains the global kill switch.");
        root.addView(locationDesc);

        globalLocationInherit = new CheckBox(this);
        globalLocationInherit.setText(fa ? "استفاده از پیش‌فرض امن سیستم (بدون Override سراسری)" :
                "Inherit safe System default (no Global override)");
        globalLocationInherit.setOnCheckedChangeListener((button, checked) -> updateGlobalLocationControls());
        root.addView(globalLocationInherit);

        globalLocationEnabled = new CheckBox(this);
        globalLocationEnabled.setText(fa ? "فعال‌سازی پیش‌فرض موقعیت برای کلون‌های بدون Override" :
                "Enable location by default for clones without an override");
        globalLocationEnabled.setOnCheckedChangeListener((button, checked) -> {
            if (checked && globalLocationInherit.isChecked()) globalLocationInherit.setChecked(false);
        });
        root.addView(globalLocationEnabled);

        globalLatitudeEt = new EditText(this);
        globalLatitudeEt.setSingleLine(true);
        globalLatitudeEt.setInputType(android.text.InputType.TYPE_CLASS_NUMBER
                | android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL
                | android.text.InputType.TYPE_NUMBER_FLAG_SIGNED);
        globalLatitudeEt.setHint("Global latitude (-90 to 90)");
        root.addView(globalLatitudeEt);

        globalLongitudeEt = new EditText(this);
        globalLongitudeEt.setSingleLine(true);
        globalLongitudeEt.setInputType(android.text.InputType.TYPE_CLASS_NUMBER
                | android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL
                | android.text.InputType.TYPE_NUMBER_FLAG_SIGNED);
        globalLongitudeEt.setHint("Global longitude (-180 to 180)");
        root.addView(globalLongitudeEt);

        resetGlobalLocationButton = new TextView(this);
        resetGlobalLocationButton.setText(fa ? "پاک‌کردن پیش‌فرض‌های موقعیت سراسری و بازگشت به سیستم" :
                "Clear Global location defaults (inherit System)");
        resetGlobalLocationButton.setTextColor(Color.parseColor("#2563EB"));
        resetGlobalLocationButton.setPadding(0, 12, 0, 18);
        resetGlobalLocationButton.setOnClickListener(v -> resetGlobalLocation());
        root.addView(resetGlobalLocationButton);

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
        if (globalLocationEnabled != null) globalLocationEnabled.setEnabled(enabled);
        if (globalLatitudeEt != null) globalLatitudeEt.setEnabled(enabled);
        if (globalLongitudeEt != null) globalLongitudeEt.setEnabled(enabled);
        if (resetGlobalLocationButton != null) resetGlobalLocationButton.setEnabled(enabled);
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
        repository.loadGlobalProfile(result -> {
            if (isFinishing() || isDestroyed()) return;
            if (!result.isSuccess()) {
                failLoading((fa ? "خواندن تنظیمات موقعیت سراسری ناموفق بود: " :
                        "Could not read Global location profile: ") + result.getMessage());
                return;
            }
            globalProfile = result.getValue();
            globalLocationInherit.setChecked(globalProfile.locationEnabled == null);
            globalLocationEnabled.setChecked(Boolean.TRUE.equals(globalProfile.locationEnabled));
            globalLatitudeEt.setText(globalProfile.latitude == null ? "" : String.valueOf(globalProfile.latitude));
            globalLongitudeEt.setText(globalProfile.longitude == null ? "" : String.valueOf(globalProfile.longitude));
            updateGlobalLocationControls();
            locationProfileLoaded = true;
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
        if (profileLoaded && locationProfileLoaded && masterGpsLoaded && !loadFailed) setControlsEnabled(true);
    }

    private void failLoading(String message) {
        loadFailed = true;
        setControlsEnabled(false);
        if (!isFinishing() && !isDestroyed())
            Toast.makeText(this, message, Toast.LENGTH_LONG).show();
    }

    private void saveSettings() {
        if (!profileLoaded || !locationProfileLoaded || !masterGpsLoaded || loadFailed) return;
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
        final Boolean locationEnabled = globalLocationInherit.isChecked()
                ? null : Boolean.valueOf(globalLocationEnabled.isChecked());
        final Double latitude;
        final Double longitude;
        try {
            latitude = globalLocationInherit.isChecked() ? null
                    : parseOptionalCoordinate(globalLatitudeEt.getText().toString(), -90.0d, 90.0d);
            longitude = globalLocationInherit.isChecked() ? null
                    : parseOptionalCoordinate(globalLongitudeEt.getText().toString(), -180.0d, 180.0d);
        } catch (IllegalArgumentException invalid) {
            saveButton.setEnabled(true);
            showSaveFailure(invalid.getMessage());
            return;
        }
        if (Boolean.TRUE.equals(locationEnabled) && (latitude == null || longitude == null)) {
            saveButton.setEnabled(true);
            showSaveFailure(fa ? "برای فعال‌سازی پیش‌فرض موقعیت، هر دو مختصات لازم است." :
                    "Both global coordinates are required when global location is enabled.");
            return;
        }

        repository.saveGlobalEnvironment(updated, profileResult -> {
            if (isFinishing() || isDestroyed()) return;
            if (!profileResult.isSuccess()) {
                saveButton.setEnabled(true);
                showSaveFailure((fa ? "پروفایل ذخیره نشد: " : "Profile was not saved: ")
                        + profileResult.getMessage());
                return;
            }
            repository.saveGlobalLocationProfile(locationEnabled, latitude, longitude, locationResult -> {
                if (isFinishing() || isDestroyed()) return;
                if (!locationResult.isSuccess()) {
                    saveButton.setEnabled(true);
                    showSaveFailure(fa
                            ? "اطلاعات دستگاه ذخیره شد، اما پروفایل موقعیت سراسری ذخیره نشد: " + locationResult.getMessage()
                            : "Device metadata was saved, but Global location profile was not: " + locationResult.getMessage());
                    return;
                }
                repository.setMasterMockGpsEnabled(masterGpsEnabled, gpsResult -> {
                    if (isFinishing() || isDestroyed()) return;
                    if (!gpsResult.isSuccess()) {
                        saveButton.setEnabled(true);
                        showSaveFailure(fa
                                ? "اطلاعات و پروفایل موقعیت ذخیره شدند، اما Master GPS ذخیره نشد؛ همگام‌سازی انجام نشد: " + gpsResult.getMessage()
                                : "Metadata and Global location profile were saved, but Master GPS was not; hooks were not synchronized: "
                                        + gpsResult.getMessage());
                        return;
                    }
                    // All three independent commits are confirmed before requesting hook synchronization.
                    CloneStore.syncAllHooks(getApplicationContext());
                    Toast.makeText(this, fa
                            ? "اطلاعات، پروفایل موقعیت و Master GPS ذخیره شدند؛ همگام‌سازی کلون‌ها درخواست شد. مشخصات دستگاه/سیم‌کارت فقط اطلاعات هستند."
                            : "Metadata, Global location profile and Master GPS were saved; clone hook synchronization was requested. Device/SIM values remain metadata only.",
                            Toast.LENGTH_LONG).show();
                    finish();
                });
            });
        });
    }

    private void updateGlobalLocationControls() {
        boolean editable = profileLoaded && locationProfileLoaded && masterGpsLoaded
                && !loadFailed && !globalLocationInherit.isChecked();
        if (globalLocationEnabled != null) globalLocationEnabled.setEnabled(editable && !loadFailed);
        if (globalLatitudeEt != null) globalLatitudeEt.setEnabled(editable && !loadFailed);
        if (globalLongitudeEt != null) globalLongitudeEt.setEnabled(editable && !loadFailed);
    }

    private Double parseOptionalCoordinate(String raw, double min, double max) {
        String value = raw == null ? "" : raw.trim();
        if (value.isEmpty()) return null;
        final double parsed;
        try {
            parsed = Double.parseDouble(value);
        } catch (NumberFormatException invalid) {
            throw new IllegalArgumentException(fa ? "مختصات باید عدد معتبر باشد." :
                    "Coordinates must be valid numbers.");
        }
        if (Double.isNaN(parsed) || Double.isInfinite(parsed) || parsed < min || parsed > max) {
            throw new IllegalArgumentException(fa ? "مختصات خارج از محدوده مجاز است." :
                    "Coordinates are outside the allowed range.");
        }
        return parsed;
    }

    private void resetGlobalLocation() {
        if (loadFailed || !locationProfileLoaded) return;
        resetGlobalLocationButton.setEnabled(false);
        saveButton.setEnabled(false);
        repository.clearGlobalLocationOverrides(result -> {
            if (isFinishing() || isDestroyed()) return;
            if (!result.isSuccess()) {
                resetGlobalLocationButton.setEnabled(true);
                saveButton.setEnabled(true);
                showSaveFailure((fa ? "پاک‌کردن پیش‌فرض‌های موقعیت ناموفق بود: " :
                        "Could not clear Global location defaults: ") + result.getMessage());
                return;
            }
            if (globalProfile == null) globalProfile = new ProfileSettings();
            globalProfile.locationEnabled = null;
            globalProfile.latitude = null;
            globalProfile.longitude = null;
            globalLocationInherit.setChecked(true);
            globalLocationEnabled.setChecked(false);
            globalLatitudeEt.setText("");
            globalLongitudeEt.setText("");
            updateGlobalLocationControls();
            CloneStore.syncAllHooks(getApplicationContext());
            Toast.makeText(this, fa
                    ? "پیش‌فرض‌های موقعیت سراسری پاک شدند؛ کلون‌ها به اولویت بعدی بازمی‌گردند."
                    : "Global location defaults cleared; clones now inherit from their next available profile source.",
                    Toast.LENGTH_LONG).show();
            resetGlobalLocationButton.setEnabled(true);
            saveButton.setEnabled(true);
        });
    }

    private void showSaveFailure(String message) {
        if (!isFinishing() && !isDestroyed())
            Toast.makeText(this, message, Toast.LENGTH_LONG).show();
    }
}
