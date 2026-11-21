package com.veyravault.space.ui;

import android.content.Intent;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import com.veyravault.space.R;
import com.veyravault.space.core.LocaleHelper;

public class AboutActivity extends BaseActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        final boolean fa = LocaleHelper.isPersian(this);

        ScrollView scroll = new ScrollView(this);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(22), dp(24), dp(22), dp(32));
        root.setBackgroundColor(UiPalette.page(this));
        scroll.addView(root);

        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setGravity(android.view.Gravity.CENTER_VERTICAL);
        TextView title = new TextView(this);
        title.setText(fa ? "دربارهٔ VeyraVault" : "About VeyraVault");
        title.setTextSize(23f);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setTextColor(UiPalette.textPrimary(this));
        header.addView(title, new LinearLayout.LayoutParams(
                0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        header.addView(createLanguageAction(fa));
        header.addView(createImmediateLockSwitch(fa));
        root.addView(header);

        addSection(root, fa ? "اطلاعات نسخه" : "Build Information",
                buildVersionSummary(fa));
        addSection(root, fa ? "وضعیت واقعی قابلیت‌ها" : "Feature Status",
                featureStatus(fa));
        addPermissionSection(root, fa);

        Button diagnostics = new Button(this);
        diagnostics.setAllCaps(false);
        diagnostics.setText(fa ? "باز کردن گزارش سازگاری" : "Open Compatibility Report");
        diagnostics.setOnClickListener(v ->
                startActivity(new Intent(AboutActivity.this, CompatibilityReportActivity.class)));
        root.addView(diagnostics, buttonParams());

        Button telegram = new Button(this);
        telegram.setAllCaps(false);
        telegram.setText("Telegram: @VaultVeyra");
        telegram.setOnClickListener(v ->
                startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse("https://t.me/VaultVeyra"))));
        root.addView(telegram, buttonParams());

        Button email = new Button(this);
        email.setAllCaps(false);
        email.setText("Email: Vaultveyra@gmail.com");
        email.setOnClickListener(v -> {
            Intent intent = new Intent(Intent.ACTION_SENDTO);
            intent.setData(Uri.parse("mailto:Vaultveyra@gmail.com"));
            startActivity(intent);
        });
        root.addView(email, buttonParams());

        setContentView(scroll);
    }

    private String buildVersionSummary(boolean fa) {
        String versionName = "unknown";
        long versionCode = -1L;
        try {
            PackageInfo info = getPackageManager().getPackageInfo(
                    getPackageName(), PackageManager.GET_PERMISSIONS);
            if (info.versionName != null) versionName = info.versionName;
            if (Build.VERSION.SDK_INT >= 28) versionCode = info.getLongVersionCode();
            else {
                //noinspection deprecation
                versionCode = info.versionCode;
            }
        } catch (PackageManager.NameNotFoundException ignored) {
            // Keep the unavailable marker rather than substituting a hard-coded build number.
        }

        int targetSdk = getApplicationInfo().targetSdkVersion;
        return (fa ? "نام بسته: " : "Application ID: ") + getPackageName()
                + (fa ? "\nنسخه: " : "\nVersion: ") + versionName
                + (fa ? "\nکد نسخه: " : "\nVersion code: ") + versionCode
                + (fa ? "\nنسخه اندروید میزبان: " : "\nHost Android: ")
                + Build.VERSION.RELEASE + " (API " + Build.VERSION.SDK_INT + ")"
                + (fa ? "\nTarget SDK: " : "\nTarget SDK: ") + targetSdk
                + (fa ? "\nحداقل نسخهٔ پشتیبانی‌شده: Android 5.0 (API 21)"
                      : "\nMinimum supported Android: Android 5.0 (API 21)");
    }

    private String featureStatus(boolean fa) {
        if (fa) {
            return "• Locale و Time Zone: پروفایل‌های Global و اختصاصی Clone با اولویت مستقل هر فیلد؛ اعمال در اجرای بعدی Clone.\n\n"
                    + "• موقعیت مکانی: تنظیم و Hook موجود است؛ نتیجه به نسخهٔ Android و API موتور وابسته است و مشاهدهٔ واقعی همهٔ برنامه‌ها روی دستگاه فیزیکی تأیید نشده است.\n\n"
                    + "• Brand / Model / SIM / Operator: برخی مقادیر فقط به‌عنوان Metadata ذخیره می‌شوند؛ موتور فعلی آن‌ها را به برنامه‌های Clone اعمال نمی‌کند.\n\n"
                    + "• VPN: برنامه در حال حاضر سرور یا تونل VPN اختصاصی ندارد؛ فقط وضعیت VPN سیستم Android را گزارش می‌کند.\n\n"
                    + "• IP عمومی: در این صفحه و Dashboard بررسی نمی‌شود و از کشور انتخاب‌شده استنتاج نمی‌شود.\n\n"
                    + "• قفل برنامه: PIN و Pattern با مشتق‌سازی رمز نسخه‌دار ذخیره می‌شوند؛ Device Admin قابل لغو است و برنامه را غیرقابل‌حذف نمی‌کند.\n\n"
                    + "• پشتیبان‌گیری و بازیابی: هنوز پیاده‌سازی نشده است.\n\n"
                    + "• GMS و سازگاری برنامه‌های ثالث: وابسته به موتور، نسخهٔ Android و خود برنامه است؛ موفقیت همهٔ سرویس‌ها تضمین نشده است.\n\n"
                    + "موفقیت CI به‌معنای تأیید همهٔ رفتارها روی دستگاه فیزیکی نیست.";
        }
        return "• Locale and Time Zone: Global and per-Clone profiles resolve each field independently and apply on the next Clone launch.\n\n"
                + "• Location: configuration and hooks exist; behavior depends on Android and engine APIs. Real observation by every target app has not been confirmed on physical devices.\n\n"
                + "• Brand / Model / SIM / Operator: some values are stored as metadata only; the current engine does not apply them to cloned apps.\n\n"
                + "• VPN: this app does not currently provide its own VPN server or tunnel. It reports Android system VPN transport status only.\n\n"
                + "• Public IP: not checked here or on the Dashboard, and never inferred from a selected country.\n\n"
                + "• App Lock: PIN and Pattern credentials use versioned password derivation. Android Device Admin is revocable and does not make the app uninstall-proof.\n\n"
                + "• Backup & Restore: not implemented yet.\n\n"
                + "• GMS and third-party app compatibility: depend on the engine, Android version, and target app; not all services are guaranteed.\n\n"
                + "A successful CI run is not proof that every behavior has been verified on a physical device.";
    }

    private void addPermissionSection(LinearLayout root, boolean fa) {
        StringBuilder details = new StringBuilder();
        try {
            PackageInfo info = getPackageManager().getPackageInfo(
                    getPackageName(), PackageManager.GET_PERMISSIONS);
            String[] permissions = info.requestedPermissions;
            int[] flags = info.requestedPermissionsFlags;
            if (permissions == null || permissions.length == 0) {
                details.append(fa ? "مجوز درخواستی ثبت‌شده‌ای پیدا نشد."
                                  : "No requested permissions were reported by PackageManager.");
            } else {
                details.append(fa ? "تعداد مجوزهای اعلام‌شده: " : "Declared permission count: ")
                        .append(permissions.length);
                for (int i = 0; i < permissions.length; i++) {
                    boolean granted = flags != null && i < flags.length
                            && (flags[i] & PackageInfo.REQUESTED_PERMISSION_GRANTED) != 0;
                    String shortName = permissions[i].substring(
                            permissions[i].lastIndexOf('.') + 1);
                    details.append("\n• ").append(shortName).append(" — ")
                            .append(granted
                                    ? (fa ? "Granted" : "Granted")
                                    : (fa ? "اعطا نشده / نیازمند بررسی" : "Not granted / review required"));
                }
            }
        } catch (PackageManager.NameNotFoundException failure) {
            details.append(fa ? "خواندن فهرست مجوزها ممکن نبود."
                              : "Could not read the requested permission list.");
        }

        addSection(root, fa ? "مجوزهای اعلام‌شده به Android" : "Permissions Declared to Android",
                details.toString());
    }

    private void addSection(LinearLayout root, String heading, String detail) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(16), dp(15), dp(16), dp(15));
        card.setBackgroundResource(R.drawable.bg_card_rounded);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        params.topMargin = dp(14);

        TextView title = new TextView(this);
        title.setText(heading);
        title.setTextSize(15f);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setTextColor(UiPalette.textPrimary(this));
        card.addView(title);

        TextView body = new TextView(this);
        body.setText(detail);
        body.setTextSize(12f);
        body.setTextColor(UiPalette.textSecondary(this));
        body.setPadding(0, dp(8), 0, 0);
        card.addView(body);
        root.addView(card, params);
    }

    private LinearLayout.LayoutParams buttonParams() {
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        params.topMargin = dp(10);
        return params;
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

}
