package com.veyravault.space.ui;

import android.app.AlertDialog;
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
import com.veyravault.space.core.ProfileResolver;
import com.veyravault.space.core.ProfileRuntimeApplier;
import com.veyravault.space.core.VirtualHookManager;

public class GlobalEnvironmentActivity extends BaseActivity {
    private AsyncCloneRepository repository;
    private com.veyravault.space.core.AsyncLocationHookRepository hookRepository;
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
    private EditText globalLocaleEt;
    private EditText globalTimeZoneEt;
    private TextView globalLocaleEffective;
    private TextView globalTimeZoneEffective;
    private Button saveGlobalLocaleButton;
    private Button resetGlobalLocaleButton;
    private Button saveGlobalTimeZoneButton;
    private Button resetGlobalTimeZoneButton;
    private boolean globalProfileFieldsBusy;
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
        hookRepository = com.veyravault.space.core.AsyncLocationHookRepository.getInstance(getApplicationContext());
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
        title.setText(fa ? "کنترل پیشرفته موقعیت و اطلاعات قدیمی" : "Advanced Location & Legacy Metadata");
        title.setTextSize(20f);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setTextColor(UiPalette.textPrimary(getApplicationContext()));
        root.addView(title);

        TextView desc = new TextView(this);
        desc.setTextSize(13f);
        desc.setTextColor(UiPalette.textSecondary(getApplicationContext()));
        desc.setPadding(0, 12, 0, 28);
        desc.setText(fa
                ? "این صفحه فقط برای کلید اصلی موقعیت و تنظیمات قدیمی سازگار است؛ تمام فیلدهای پروفایل سراسری را از گزینه «پروفایل کامل محیط» مدیریت کنید. مدل دستگاه، کشور و اپراتور در این نسخه فقط اطلاعات ذخیره‌شده‌اند و توسط موتور روی کلون‌ها اعمال نمی‌شوند. موقعیت هر کلون جداگانه و با API محدود به بسته و کاربر مجازی تنظیم می‌شود. این گزینه محدودیت منطقه‌ای سرویس‌های دیگر را دور نمی‌زند."
                : "This page is limited to the Master Location switch and legacy-compatible controls; use Complete Environment Profile for the full Global field registry. Device model, country and operator are stored metadata only and are not applied to clones. Clone locations use the Engine's package- and virtual-user-scoped API. This setting does not bypass third-party regional restrictions.");
        root.addView(desc);

        root.addView(buildGlobalLocaleTimeZoneSection());

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
        locationDesc.setTextColor(UiPalette.textSecondary(getApplicationContext()));
        locationDesc.setText(fa
                ? "اولویت هر فیلد: تنظیم اختصاصی کلون، سپس این پروفایل سراسری، سپس مقدار امن سیستم. Master Mock GPS کلید قطع‌کننده اصلی است."
                : "Per-field priority: Clone override, then this Global profile, then the safe system default. Master Mock GPS remains the global kill switch.");
        root.addView(locationDesc);

        globalLocationInherit = new CheckBox(this);
        globalLocationInherit.setText(fa ? "استفاده از پیش‌فرض امن سیستم (بدون Override سراسری)" :
                "Inherit Safe Isolated Default (no Global override)");
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
                "Clear Global location defaults (inherit Safe Isolated Default)");
        resetGlobalLocationButton.setTextColor(UiPalette.accent(getApplicationContext()));
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


    private View buildGlobalLocaleTimeZoneSection() {
        LinearLayout section = new LinearLayout(this);
        section.setOrientation(LinearLayout.VERTICAL);
        section.setPadding(0, 0, 0, 16);

        TextView title = new TextView(this);
        title.setText(fa ? "پیش‌فرض‌های زبان و منطقه زمانی سراسری"
                : "Global Locale & Time Zone Defaults");
        title.setTextSize(18f);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setTextColor(UiPalette.textPrimary(getApplicationContext()));
        section.addView(title);

        TextView description = new TextView(this);
        description.setTextSize(13f);
        description.setTextColor(UiPalette.textSecondary(getApplicationContext()));
        description.setPadding(0, 8, 0, 12);
        description.setText(fa
                ? "این مقادیر برای کلون‌هایی استفاده می‌شوند که Override اختصاصی ندارند. مقدار اختصاصی هر کلون همیشه اولویت دارد. پاک‌کردن یک فیلد سراسری فقط همان پیش‌فرض را حذف می‌کند و مقدار سیستم جایگزین می‌شود."
                : "These defaults apply only when a clone has no per-clone override. Clone-specific values always take precedence. Reset clears only the selected Global default and reveals the Safe Isolated Default value.");
        section.addView(description);

        section.addView(buildGlobalProfileField(true));
        section.addView(buildGlobalProfileField(false));
        return section;
    }

    private View buildGlobalProfileField(boolean locale) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(16, 12, 16, 16);
        card.setBackgroundResource(R.drawable.bg_card_rounded);
        LinearLayout.LayoutParams cardParams = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        cardParams.bottomMargin = 12;
        card.setLayoutParams(cardParams);

        TextView heading = new TextView(this);
        heading.setText(locale ? (fa ? "زبان پیش‌فرض (Locale)" : "Default Locale")
                : (fa ? "منطقه زمانی پیش‌فرض (Time Zone)" : "Default Time Zone"));
        heading.setTextSize(16f);
        heading.setTypeface(Typeface.DEFAULT_BOLD);
        heading.setTextColor(UiPalette.textPrimary(getApplicationContext()));
        card.addView(heading);

        TextView effective = new TextView(this);
        effective.setTextSize(12f);
        effective.setTextColor(UiPalette.textSecondary(getApplicationContext()));
        effective.setPadding(0, 6, 0, 8);
        card.addView(effective);
        if (locale) globalLocaleEffective = effective;
        else globalTimeZoneEffective = effective;

        EditText input = new EditText(this);
        input.setSingleLine(true);
        input.setTextSize(15f);
        input.setHint(locale ? "e.g. en-US, fa-IR, de-DE"
                : "e.g. America/New_York, Asia/Tehran, UTC");
        card.addView(input);
        if (locale) globalLocaleEt = input;
        else globalTimeZoneEt = input;

        Button presets = new Button(this);
        presets.setAllCaps(false);
        presets.setText(fa ? "انتخاب مقدار آماده" : "Choose a preset");
        presets.setOnClickListener(v -> showGlobalProfilePresets(locale));
        card.addView(presets);

        LinearLayout actions = new LinearLayout(this);
        actions.setOrientation(LinearLayout.HORIZONTAL);

        Button save = new Button(this);
        save.setAllCaps(false);
        save.setText(fa ? "ذخیره پیش‌فرض" : "Save Global default");
        save.setOnClickListener(v -> saveGlobalProfileField(locale));
        actions.addView(save, new LinearLayout.LayoutParams(
                0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        Button reset = new Button(this);
        reset.setAllCaps(false);
        reset.setText(fa ? "بازگشت به سیستم" : "Reset to Safe Default");
        reset.setOnClickListener(v -> resetGlobalProfileField(locale));
        actions.addView(reset, new LinearLayout.LayoutParams(
                0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        card.addView(actions);
        if (locale) {
            saveGlobalLocaleButton = save;
            resetGlobalLocaleButton = reset;
        } else {
            saveGlobalTimeZoneButton = save;
            resetGlobalTimeZoneButton = reset;
        }
        return card;
    }

    private void setGlobalProfileControlsEnabled(boolean enabled) {
        boolean ready = enabled && profileLoaded && locationProfileLoaded
                && masterGpsLoaded && !loadFailed && !globalProfileFieldsBusy
                && globalProfile != null;
        if (globalLocaleEt != null) globalLocaleEt.setEnabled(ready);
        if (globalTimeZoneEt != null) globalTimeZoneEt.setEnabled(ready);
        if (saveGlobalLocaleButton != null) saveGlobalLocaleButton.setEnabled(ready);
        if (saveGlobalTimeZoneButton != null) saveGlobalTimeZoneButton.setEnabled(ready);
        if (resetGlobalLocaleButton != null) {
            resetGlobalLocaleButton.setEnabled(ready && globalProfile.localeTag != null);
        }
        if (resetGlobalTimeZoneButton != null) {
            resetGlobalTimeZoneButton.setEnabled(ready && globalProfile.timeZoneId != null);
        }
    }

    private void updateGlobalProfileEffectiveValues() {
        if (globalProfile == null) return;
        ProfileResolver.ResolvedProfile effective = ProfileResolver.resolve(
                new ProfileSettings(), globalProfile, ProfileRuntimeApplier.systemFallback());
        String localeValue = effective.localeTag == null ? "UNSET" : effective.localeTag;
        String timeZoneValue = effective.timeZoneId == null ? "UNSET" : effective.timeZoneId;
        globalLocaleEffective.setText((fa ? "مقدار مؤثر: " : "Effective: ") + localeValue
                + "  |  " + (fa ? "منبع: " : "Source: ") + effective.localeSource);
        globalTimeZoneEffective.setText((fa ? "مقدار مؤثر: " : "Effective: ") + timeZoneValue
                + "  |  " + (fa ? "منبع: " : "Source: ") + effective.timeZoneSource);
        setGlobalProfileControlsEnabled(!loadFailed);
    }

    private void saveGlobalProfileField(boolean locale) {
        if (loadFailed || !locationProfileLoaded || globalProfile == null || globalProfileFieldsBusy) return;
        String value = (locale ? globalLocaleEt : globalTimeZoneEt).getText().toString().trim();
        if (value.isEmpty()) {
            showSaveFailure(fa ? "برای حذف پیش‌فرض از دکمه بازگشت به سیستم استفاده کنید."
                    : "Use Reset to Safe Default to clear this Global default.");
            return;
        }
        if (locale && !ProfileSettings.isLocaleTagValid(value)) {
            showSaveFailure(fa ? "Locale معتبر نیست؛ نمونه: fa-IR یا en-US."
                    : "Invalid BCP-47 locale tag; examples: en-US or fa-IR.");
            return;
        }
        if (!locale && !ProfileSettings.isTimeZoneIdValid(value)) {
            showSaveFailure(fa ? "شناسه منطقه زمانی معتبر نیست؛ از شناسه‌های IANA استفاده کنید."
                    : "Invalid time-zone ID; use an IANA time-zone identifier.");
            return;
        }

        ProfileSettings update = new ProfileSettings();
        if (locale) update.localeTag = value;
        else update.timeZoneId = value;

        globalProfileFieldsBusy = true;
        setGlobalProfileControlsEnabled(false);
        repository.saveGlobalProfile(update, result -> {
            if (isFinishing() || isDestroyed()) return;
            if (!result.isSuccess()) {
                globalProfileFieldsBusy = false;
                setGlobalProfileControlsEnabled(true);
                showSaveFailure((fa ? "ذخیره پیش‌فرض سراسری ناموفق بود: "
                        : "Could not save Global default: ") + result.getMessage());
                return;
            }
            reloadGlobalProfileAfterFieldMutation(locale, false);
        });
    }

    private void resetGlobalProfileField(boolean locale) {
        if (loadFailed || !locationProfileLoaded || globalProfile == null || globalProfileFieldsBusy) return;
        String field = locale ? "localeTag" : "timeZoneId";
        globalProfileFieldsBusy = true;
        setGlobalProfileControlsEnabled(false);
        repository.clearGlobalProfileField(field, result -> {
            if (isFinishing() || isDestroyed()) return;
            if (!result.isSuccess()) {
                globalProfileFieldsBusy = false;
                setGlobalProfileControlsEnabled(true);
                showSaveFailure((fa ? "بازنشانی پیش‌فرض سراسری ناموفق بود: "
                        : "Could not reset Global default: ") + result.getMessage());
                return;
            }
            reloadGlobalProfileAfterFieldMutation(locale, true);
        });
    }

    private void reloadGlobalProfileAfterFieldMutation(boolean locale, boolean reset) {
        repository.loadGlobalProfile(result -> {
            if (isFinishing() || isDestroyed()) return;
            if (!result.isSuccess() || result.getValue() == null) {
                failLoading((fa ? "تغییر ذخیره شد اما بازخوانی پروفایل ناموفق بود: "
                        : "The change was saved, but reloading the Global profile failed: ")
                        + result.getMessage());
                return;
            }
            globalProfile = result.getValue().copy();
            globalLocaleEt.setText(globalProfile.localeTag == null ? "" : globalProfile.localeTag);
            globalTimeZoneEt.setText(globalProfile.timeZoneId == null ? "" : globalProfile.timeZoneId);
            updateGlobalProfileEffectiveValues();
            globalProfileFieldsBusy = false;
            setGlobalProfileControlsEnabled(true);
            Toast.makeText(this, reset
                    ? (fa ? "فقط پیش‌فرض همین فیلد حذف شد؛ مقدار سیستم مؤثر است و Override کلون‌ها حفظ شد."
                            : "Only this Global field was cleared. Safe Isolated Default now applies; clone overrides are unchanged.")
                    : (fa ? "پیش‌فرض سراسری ذخیره شد؛ Overrideهای کلون حفظ شدند و در اجرای بعدی اعمال می‌شود."
                            : "Global default saved. Clone overrides are preserved; the default applies on the next clone launch."),
                    Toast.LENGTH_LONG).show();
        });
    }

    private void showGlobalProfilePresets(boolean locale) {
        final String[] values = locale
                ? new String[]{"en-US", "en-GB", "fa-IR", "de-DE", "fr-FR", "tr-TR", "ar-AE", "ja-JP"}
                : new String[]{"UTC", "Asia/Tehran", "America/New_York", "Europe/London",
                        "Europe/Berlin", "Europe/Istanbul", "Asia/Dubai", "Asia/Tokyo"};
        new AlertDialog.Builder(this)
                .setTitle(locale ? (fa ? "انتخاب زبان پیش‌فرض" : "Choose Default Locale")
                        : (fa ? "انتخاب منطقه زمانی پیش‌فرض" : "Choose Default Time Zone"))
                .setItems(values, (dialog, which) ->
                        (locale ? globalLocaleEt : globalTimeZoneEt).setText(values[which]))
                .show();
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
        setGlobalProfileControlsEnabled(enabled);
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
            globalProfile = result.getValue().copy();
            globalLocaleEt.setText(globalProfile.localeTag == null ? "" : globalProfile.localeTag);
            globalTimeZoneEt.setText(globalProfile.timeZoneId == null ? "" : globalProfile.timeZoneId);
            updateGlobalProfileEffectiveValues();
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
                    hookRepository.syncAllCloneLocationHooks((summary, error) -> {
                        if (isFinishing() || isDestroyed()) return;
                        if (error != null || summary == null) {
                            saveButton.setEnabled(true);
                            showSaveFailure(fa
                                    ? "تنظیمات ذخیره شدند اما همگام‌سازی کلون‌ها اجرا نشد: "
                                            + (error == null ? "No hook summary" : error)
                                    : "Settings were saved, but clone hook synchronization could not run: "
                                            + (error == null ? "No hook summary" : error));
                            return;
                        }
                        Toast.makeText(this, fa
                                ? "اطلاعات و تنظیمات ذخیره شدند. نتیجه Hookها: " + formatSyncSummary(summary)
                                        + " مشخصات دستگاه/سیم‌کارت فقط اطلاعات هستند."
                                : "Metadata and Global location settings were saved. Hook outcomes: "
                                        + formatSyncSummary(summary) + " Device/SIM values remain metadata only.",
                                Toast.LENGTH_LONG).show();
                        finish();
                    });
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

    private String formatSyncSummary(VirtualHookManager.SyncSummary summary) {
        if (summary == null) return fa ? "نتیجه‌ای دریافت نشد." : "No sync summary was returned.";
        if (!summary.registryReadable) return fa
                ? "همگام‌سازی انجام نشد؛ فهرست کلون‌ها قابل خواندن نیست: " + summary.detail
                : "No hooks synchronized; clone registry is unreadable: " + summary.detail;
        return fa
                ? "اعمال‌شده=" + summary.applied + "، غیرفعال=" + summary.disabled
                        + "، پشتیبانی‌نشده=" + summary.unsupported + "، ناموفق=" + summary.failed
                : "applied=" + summary.applied + ", disabled=" + summary.disabled
                        + ", unsupported=" + summary.unsupported + ", failed=" + summary.failed;
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
            hookRepository.syncAllCloneLocationHooks((summary, error) -> {
                if (isFinishing() || isDestroyed()) return;
                if (error != null || summary == null) {
                    resetGlobalLocationButton.setEnabled(true);
                    saveButton.setEnabled(true);
                    showSaveFailure((fa ? "پیش‌فرض‌ها پاک شدند اما همگام‌سازی اجرا نشد: " :
                            "Global defaults were cleared, but hook synchronization could not run: ")
                            + (error == null ? "No hook summary" : error));
                    return;
                }
                Toast.makeText(this, fa
                        ? "پیش‌فرض‌های موقعیت سراسری پاک شدند. نتیجه Hookها: " + formatSyncSummary(summary)
                        : "Global location defaults cleared. Hook outcomes: " + formatSyncSummary(summary),
                        Toast.LENGTH_LONG).show();
                resetGlobalLocationButton.setEnabled(true);
                saveButton.setEnabled(true);
            });
        });
    }

    private void showSaveFailure(String message) {
        if (!isFinishing() && !isDestroyed())
            Toast.makeText(this, message, Toast.LENGTH_LONG).show();
    }
}
