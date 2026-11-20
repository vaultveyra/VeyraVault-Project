package com.veyravault.space.ui;

import android.content.Intent;
import android.graphics.Typeface;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.RadioButton;
import android.widget.RadioGroup;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import com.veyravault.space.core.AppearanceManager;
import com.veyravault.space.core.LocaleHelper;

public class SettingsHubActivity extends BaseActivity {
    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        final boolean fa = LocaleHelper.isPersian(this);

        ScrollView scroll = new ScrollView(this);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(24), dp(24), dp(24), dp(32));
        root.setBackgroundColor(UiPalette.page(this));
        scroll.addView(root);

        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setGravity(android.view.Gravity.CENTER_VERTICAL);
        TextView title = new TextView(this);
        title.setText(fa ? "تنظیمات" : "Settings");
        title.setTextSize(24f);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setTextColor(UiPalette.textPrimary(this));
        header.addView(title, new LinearLayout.LayoutParams(
                0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        header.addView(createImmediateLockAction(fa));
        root.addView(header);

        addAppearanceSection(root, fa);
        addRow(root, fa ? "آیکون و نام لانچر" : "Launcher Icon & Label",
                fa ? "انتخاب از میان گزینه‌های واقعی بسته‌بندی‌شده در برنامه"
                   : "Choose from the launcher options actually bundled in this app",
                AppIconNameActivity.class);
        addRow(root, fa ? "محیط و پروفایل سراسری" : "Global Environment",
                fa ? "مدیریت تنظیمات عمومی محیط" : "Manage global environment preferences",
                GlobalEnvironmentActivity.class);
        addRow(root, fa ? "امنیت و قفل برنامه" : "Security & App Lock",
                fa ? "مدیریت قفل و گزینه‌های امنیتی" : "Manage app lock and security options",
                SecuritySettingsActivity.class);
        addRow(root, fa ? "مجوزها و شفافیت" : "Permissions & Transparency",
                fa ? "مشاهده وضعیت مجوزهای برنامه" : "Review app permission status",
                PermissionsActivity.class);
        addRow(root, fa ? "درباره برنامه و گزارش سازگاری" : "About & Compatibility",
                fa ? "اطلاعات نسخه و عیب‌یابی خواندنی" : "Version information and read-only diagnostics",
                AboutActivity.class);
        addRow(root, fa ? "بررسی رزروهای معلق" : "Pending Clone ID reservations",
                fa ? "بررسی وضعیت موتور و آزادسازی دستی شناسه‌های امن"
                   : "Inspect Engine state and manually release only confirmed-absent reservations",
                PendingReservationsActivity.class);
        addFutureBackupSection(root, fa);
        addLanguageSection(root, fa);
        setContentView(scroll);
    }

    private void addAppearanceSection(LinearLayout root, boolean fa) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(18), dp(16), dp(18), dp(16));
        card.setBackgroundResource(com.veyravault.space.R.drawable.bg_card_rounded);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        params.topMargin = dp(18);

        TextView heading = new TextView(this);
        heading.setText(fa ? "ظاهر برنامه" : "Appearance");
        heading.setTextSize(16f);
        heading.setTypeface(Typeface.DEFAULT_BOLD);
        heading.setTextColor(UiPalette.textPrimary(this));
        card.addView(heading);

        TextView detail = new TextView(this);
        detail.setText(fa
                ? "تم سیستم، روشن یا تاریک را انتخاب کنید. انتخاب شما ذخیره می‌شود و روی صفحه‌های برنامه اعمال خواهد شد."
                : "Choose System, Light, or Dark. Your selection is saved and applied across the app.");
        detail.setTextSize(12f);
        detail.setTextColor(UiPalette.textSecondary(this));
        detail.setPadding(0, dp(6), 0, dp(10));
        card.addView(detail);

        RadioGroup choices = new RadioGroup(this);
        choices.setOrientation(RadioGroup.HORIZONTAL);
        RadioButton system = new RadioButton(this);
        system.setId(View.generateViewId());
        system.setText(fa ? "سیستم" : "System");
        RadioButton light = new RadioButton(this);
        light.setId(View.generateViewId());
        light.setText(fa ? "روشن" : "Light");
        RadioButton dark = new RadioButton(this);
        dark.setId(View.generateViewId());
        dark.setText(fa ? "تاریک" : "Dark");
        choices.addView(system, new RadioGroup.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        choices.addView(light, new RadioGroup.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        choices.addView(dark, new RadioGroup.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        String saved = AppearanceManager.getThemeMode(this);
        if (AppearanceManager.MODE_LIGHT.equals(saved)) choices.check(light.getId());
        else if (AppearanceManager.MODE_DARK.equals(saved)) choices.check(dark.getId());
        else choices.check(system.getId());

        choices.setOnCheckedChangeListener((group, checkedId) -> {
            String mode = checkedId == light.getId() ? AppearanceManager.MODE_LIGHT
                    : checkedId == dark.getId() ? AppearanceManager.MODE_DARK
                    : AppearanceManager.MODE_SYSTEM;
            if (!AppearanceManager.setThemeMode(SettingsHubActivity.this, mode)) {
                Toast.makeText(SettingsHubActivity.this,
                        fa ? "ذخیره تنظیم ظاهر ناموفق بود." : "Could not save the appearance setting.",
                        Toast.LENGTH_LONG).show();
            }
        });
        card.addView(choices);
        root.addView(card, params);
    }

    private void addLanguageSection(LinearLayout root, boolean fa) {
        LinearLayout language = new LinearLayout(this);
        language.setOrientation(LinearLayout.VERTICAL);
        language.setPadding(dp(18), dp(16), dp(18), dp(16));
        language.setBackgroundResource(com.veyravault.space.R.drawable.bg_card_rounded);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        params.topMargin = dp(18);

        TextView label = new TextView(this);
        label.setText(fa ? "زبان برنامه" : "App Language");
        label.setTextSize(16f);
        label.setTypeface(Typeface.DEFAULT_BOLD);
        label.setTextColor(UiPalette.textPrimary(this));
        language.addView(label);

        TextView toggle = new TextView(this);
        toggle.setText(fa ? "Switch to English" : "تغییر به فارسی");
        toggle.setTextSize(14f);
        toggle.setTextColor(UiPalette.accent(this));
        toggle.setPadding(0, dp(12), 0, 0);
        toggle.setOnClickListener(v -> {
            LocaleHelper.toggleLanguage(SettingsHubActivity.this);
            recreate();
        });
        language.addView(toggle);
        root.addView(language, params);
    }

    private void addFutureBackupSection(LinearLayout root, boolean fa) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(18), dp(16), dp(18), dp(16));
        card.setBackgroundResource(com.veyravault.space.R.drawable.bg_card_rounded);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        params.topMargin = dp(18);

        TextView heading = new TextView(this);
        heading.setText(fa ? "پشتیبان‌گیری و بازیابی داده‌ها" : "Backup & Restore");
        heading.setTextSize(16f);
        heading.setTypeface(Typeface.DEFAULT_BOLD);
        heading.setTextColor(UiPalette.textPrimary(this));
        card.addView(heading);

        TextView detail = new TextView(this);
        detail.setText(fa
                ? "محل این قابلیت برای توسعه آینده رزرو شده است. هنوز هیچ نسخه پشتیبان یا بازیابی انجام نمی‌شود و داده‌ای تغییر نمی‌کند."
                : "Reserved for a future release. Backup and restore are not active yet; no data is read, written, exported or restored.");
        detail.setTextSize(12f);
        detail.setTextColor(UiPalette.textSecondary(this));
        detail.setPadding(0, dp(6), 0, 0);
        card.addView(detail);
        root.addView(card, params);
    }

    private void addRow(LinearLayout root, String heading, String detail, final Class<?> target) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(18), dp(16), dp(18), dp(16));
        card.setBackgroundResource(com.veyravault.space.R.drawable.bg_card_rounded);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        params.topMargin = dp(14);

        TextView title = new TextView(this);
        title.setText(heading);
        title.setTextSize(16f);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setTextColor(UiPalette.textPrimary(this));
        card.addView(title);

        TextView description = new TextView(this);
        description.setText(detail);
        description.setTextSize(12f);
        description.setTextColor(UiPalette.textSecondary(this));
        description.setPadding(0, dp(6), 0, 0);
        card.addView(description);

        card.setOnClickListener(v ->
                startActivity(new Intent(SettingsHubActivity.this, target)));
        root.addView(card, params);
    }
}
