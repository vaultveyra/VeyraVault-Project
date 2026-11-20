package com.veyravault.space.ui;

import android.app.AlertDialog;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import com.veyravault.space.core.AsyncCloneRepository;
import com.veyravault.space.core.CloneStore;
import com.veyravault.space.core.LocaleHelper;
import com.veyravault.space.core.ProfileResolver;
import com.veyravault.space.core.ProfileRuntimeApplier;
import com.veyravault.space.core.ProfileSettings;

import java.util.List;
import java.util.Locale;
import java.util.TimeZone;

/**
 * Per-clone Locale and Time Zone editor.
 * Changes are persisted asynchronously and take effect on the next clone process launch.
 * This screen never stops a clone or modifies package/session data.
 */
public class CloneEnvironmentProfileActivity extends BaseActivity {
    private AsyncCloneRepository repository;
    private boolean fa;
    private String packageName;
    private int userId;
    private boolean cloneLoaded;
    private boolean globalLoaded;
    private boolean registryLoaded;
    private boolean loadFailed;
    private ProfileSettings cloneProfile;
    private ProfileSettings globalProfile;
    private EditText localeInput;
    private EditText timeZoneInput;
    private TextView localeEffective;
    private TextView timeZoneEffective;
    private Button localeSave;
    private Button localeReset;
    private Button timeZoneSave;
    private Button timeZoneReset;

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        fa = LocaleHelper.isPersian(this);
        packageName = getIntent().getStringExtra("pkg");
        userId = getIntent().getIntExtra("uid", -1);
        if (packageName == null || packageName.trim().isEmpty() || userId < 0) {
            Toast.makeText(this, fa ? "شناسه کلون معتبر نیست." : "Clone identity is invalid.",
                    Toast.LENGTH_LONG).show();
            finish();
            return;
        }
        repository = AsyncCloneRepository.getInstance(getApplicationContext());
        buildUi();
        setControlsEnabled(false);
        loadProfiles();
    }

    private void buildUi() {
        ScrollView scroll = new ScrollView(this);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(20), dp(24), dp(20), dp(36));
        root.setBackgroundColor(UiPalette.page(getApplicationContext()));
        scroll.addView(root);

        TextView title = new TextView(this);
        title.setText(fa ? "محیط اختصاصی کلون" : "Clone Environment Profile");
        title.setTextSize(22f);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setTextColor(UiPalette.textPrimary(getApplicationContext()));
        root.addView(title);

        TextView intro = new TextView(this);
        intro.setText(fa
                ? "زبان و منطقه زمانی فقط برای همین بسته و شناسه مجازی تنظیم می‌شوند. اولویت هر فیلد: کلون ← سراسری ← سیستم. تغییرات پس از اجرای بعدی کلون اعمال می‌شوند؛ این صفحه نشست فعال را متوقف نمی‌کند."
                : "Locale and time zone are scoped to this virtual package and user. Each field resolves Clone → Global → System. Saved changes apply on the next clone launch; this screen does not stop an active session.");
        intro.setTextSize(13f);
        intro.setTextColor(UiPalette.textSecondary(getApplicationContext()));
        intro.setPadding(0, dp(10), 0, dp(18));
        root.addView(intro);

        root.addView(buildFieldCard(true));
        root.addView(buildFieldCard(false));
        setContentView(scroll);
    }

    private View buildFieldCard(boolean locale) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(18), dp(16), dp(18), dp(18));
        card.setBackgroundResource(com.veyravault.space.R.drawable.bg_card_rounded);
        LinearLayout.LayoutParams cardLp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        cardLp.bottomMargin = dp(16);
        card.setLayoutParams(cardLp);

        TextView heading = new TextView(this);
        heading.setText(locale ? (fa ? "زبان (Locale)" : "Locale")
                : (fa ? "منطقه زمانی (Time Zone)" : "Time Zone"));
        heading.setTextSize(17f);
        heading.setTypeface(Typeface.DEFAULT_BOLD);
        heading.setTextColor(UiPalette.textPrimary(getApplicationContext()));
        card.addView(heading);

        TextView effective = new TextView(this);
        effective.setTextSize(13f);
        effective.setTextColor(UiPalette.textSecondary(getApplicationContext()));
        effective.setPadding(0, dp(8), 0, dp(8));
        card.addView(effective);
        if (locale) localeEffective = effective; else timeZoneEffective = effective;

        EditText input = new EditText(this);
        input.setSingleLine(true);
        input.setTextSize(15f);
        input.setHint(locale ? "e.g. en-US, fa-IR, de-DE" : "e.g. America/New_York, Asia/Tehran, UTC");
        card.addView(input);
        if (locale) localeInput = input; else timeZoneInput = input;

        Button presets = new Button(this);
        presets.setAllCaps(false);
        presets.setText(fa ? "انتخاب مقدار آماده" : "Choose a preset");
        presets.setOnClickListener(v -> showPresets(locale));
        card.addView(presets);

        LinearLayout actions = new LinearLayout(this);
        actions.setOrientation(LinearLayout.HORIZONTAL);
        Button save = new Button(this);
        save.setAllCaps(false);
        save.setText(fa ? "ذخیره این فیلد" : "Save this field");
        save.setOnClickListener(v -> saveField(locale));
        actions.addView(save, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        Button reset = new Button(this);
        reset.setAllCaps(false);
        reset.setText(fa ? "بازگشت به Global" : "Reset to Global");
        reset.setOnClickListener(v -> resetField(locale));
        actions.addView(reset, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        card.addView(actions);
        if (locale) { localeSave = save; localeReset = reset; }
        else { timeZoneSave = save; timeZoneReset = reset; }
        return card;
    }

    private void loadProfiles() {
        repository.loadClones(result -> {
            if (isFinishing() || isDestroyed()) return;
            if (!result.isSuccess() || result.getValue() == null) {
                failLoad((fa ? "خواندن فهرست کلون‌ها ناموفق بود: " : "Could not read clone registry: ")
                        + result.getMessage());
                return;
            }
            boolean found = false;
            for (CloneStore.CloneEntry entry : result.getValue()) {
                if (entry != null && packageName.equals(entry.packageName) && userId == entry.userId) {
                    found = true;
                    break;
                }
            }
            if (!found) {
                failLoad(fa ? "کلون در فهرست معتبر پیدا نشد." : "The requested clone is not in the validated registry.");
                return;
            }
            registryLoaded = true;
            finishLoadIfReady();
        });
        repository.loadCloneProfile(packageName, userId, result -> {
            if (isFinishing() || isDestroyed()) return;
            if (!result.isSuccess() || result.getValue() == null) {
                failLoad((fa ? "خواندن تنظیمات کلون ناموفق بود: " : "Could not read clone profile: ")
                        + result.getMessage());
                return;
            }
            cloneProfile = result.getValue();
            cloneLoaded = true;
            finishLoadIfReady();
        });
        repository.loadGlobalProfile(result -> {
            if (isFinishing() || isDestroyed()) return;
            if (!result.isSuccess() || result.getValue() == null) {
                failLoad((fa ? "خواندن پروفایل سراسری ناموفق بود: " : "Could not read Global profile: ")
                        + result.getMessage());
                return;
            }
            globalProfile = result.getValue();
            globalLoaded = true;
            finishLoadIfReady();
        });
    }

    private void finishLoadIfReady() {
        if (!registryLoaded || !cloneLoaded || !globalLoaded || loadFailed) return;
        localeInput.setText(cloneProfile.localeTag == null ? "" : cloneProfile.localeTag);
        timeZoneInput.setText(cloneProfile.timeZoneId == null ? "" : cloneProfile.timeZoneId);
        updateEffectiveValues();
        setControlsEnabled(true);
    }

    private void updateEffectiveValues() {
        ProfileResolver.ResolvedProfile effective = ProfileResolver.resolve(
                cloneProfile, globalProfile, ProfileRuntimeApplier.systemFallback());
        String localeValue = effective.localeTag == null ? "UNSET" : effective.localeTag;
        String zoneValue = effective.timeZoneId == null ? "UNSET" : effective.timeZoneId;
        localeEffective.setText((fa ? "مقدار مؤثر: " : "Effective: ") + localeValue
                + "  |  " + (fa ? "منبع: " : "Source: ") + effective.localeSource);
        timeZoneEffective.setText((fa ? "مقدار مؤثر: " : "Effective: ") + zoneValue
                + "  |  " + (fa ? "منبع: " : "Source: ") + effective.timeZoneSource);
        localeReset.setEnabled(cloneProfile.localeTag != null);
        timeZoneReset.setEnabled(cloneProfile.timeZoneId != null);
    }

    private void saveField(boolean locale) {
        if (!isReady()) return;
        String value = (locale ? localeInput : timeZoneInput).getText().toString().trim();
        if (value.isEmpty()) {
            Toast.makeText(this, fa ? "برای حذف Override از دکمه Reset to Global استفاده کنید."
                    : "Use Reset to Global to remove this override.", Toast.LENGTH_LONG).show();
            return;
        }
        if (locale && !ProfileSettings.isLocaleTagValid(value)) {
            showValidationError(fa ? "Locale معتبر نیست؛ نمونه: fa-IR یا en-US."
                    : "Invalid BCP-47 locale tag; examples: en-US or fa-IR.");
            return;
        }
        if (!locale && !ProfileSettings.isTimeZoneIdValid(value)) {
            showValidationError(fa ? "شناسه منطقه زمانی معتبر نیست؛ از فهرست مناطق IANA استفاده کنید."
                    : "Invalid time-zone ID; use an IANA time-zone identifier.");
            return;
        }
        setControlsEnabled(false);
        ProfileSettings update = new ProfileSettings();
        if (locale) update.localeTag = value; else update.timeZoneId = value;
        repository.saveCloneProfile(packageName, userId, update, result -> {
            if (isFinishing() || isDestroyed()) return;
            if (!result.isSuccess()) {
                setControlsEnabled(true);
                showValidationError((fa ? "ذخیره ناموفق بود: " : "Save failed: ") + result.getMessage());
                return;
            }
            reloadAfterMutation(locale, value, false);
        });
    }

    private void resetField(boolean locale) {
        if (!isReady()) return;
        String field = locale ? "localeTag" : "timeZoneId";
        setControlsEnabled(false);
        repository.clearCloneProfileField(packageName, userId, field, result -> {
            if (isFinishing() || isDestroyed()) return;
            if (!result.isSuccess()) {
                setControlsEnabled(true);
                showValidationError((fa ? "بازنشانی ناموفق بود: " : "Reset failed: ") + result.getMessage());
                return;
            }
            reloadAfterMutation(locale, "", true);
        });
    }

    private void reloadAfterMutation(boolean locale, String value, boolean reset) {
        repository.loadCloneProfile(packageName, userId, result -> {
            if (isFinishing() || isDestroyed()) return;
            if (!result.isSuccess() || result.getValue() == null) {
                failLoad((fa ? "ذخیره انجام شد اما بازخوانی پروفایل ناموفق بود: "
                        : "Saved, but reloading the profile failed: ") + result.getMessage());
                return;
            }
            cloneProfile = result.getValue();
            if (locale) localeInput.setText(cloneProfile.localeTag == null ? "" : cloneProfile.localeTag);
            else timeZoneInput.setText(cloneProfile.timeZoneId == null ? "" : cloneProfile.timeZoneId);
            updateEffectiveValues();
            setControlsEnabled(true);
            Toast.makeText(this, reset
                    ? (fa ? "Override این فیلد حذف شد؛ مقدار Global/System مؤثر است."
                          : "Field override cleared; Global/System now applies.")
                    : (fa ? "ذخیره شد؛ در اجرای بعدی کلون اعمال می‌شود."
                          : "Saved; this setting applies on the clone's next launch."),
                    Toast.LENGTH_LONG).show();
        });
    }

    private void showPresets(boolean locale) {
        final String[] values = locale
                ? new String[]{"en-US", "fa-IR", "de-DE", "fr-FR", "tr-TR", "ar-AE", "ja-JP"}
                : new String[]{"UTC", "Asia/Tehran", "America/New_York", "Europe/London",
                        "Europe/Berlin", "Europe/Istanbul", "Asia/Dubai", "Asia/Tokyo"};
        new AlertDialog.Builder(this)
                .setTitle(locale ? (fa ? "انتخاب زبان" : "Choose Locale")
                        : (fa ? "انتخاب منطقه زمانی" : "Choose Time Zone"))
                .setItems(values, (dialog, which) ->
                        (locale ? localeInput : timeZoneInput).setText(values[which]))
                .show();
    }

    private void setControlsEnabled(boolean enabled) {
        if (localeInput == null) return;
        localeInput.setEnabled(enabled);
        timeZoneInput.setEnabled(enabled);
        localeSave.setEnabled(enabled);
        timeZoneSave.setEnabled(enabled);
        localeReset.setEnabled(enabled && cloneProfile != null && cloneProfile.localeTag != null);
        timeZoneReset.setEnabled(enabled && cloneProfile != null && cloneProfile.timeZoneId != null);
    }

    private boolean isReady() { return !loadFailed && registryLoaded && cloneLoaded && globalLoaded; }

    private void failLoad(String message) {
        loadFailed = true;
        setControlsEnabled(false);
        if (!isFinishing() && !isDestroyed())
            Toast.makeText(this, message, Toast.LENGTH_LONG).show();
    }

    private void showValidationError(String message) {
        Toast.makeText(this, message, Toast.LENGTH_LONG).show();
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}
