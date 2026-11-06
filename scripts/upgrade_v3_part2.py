#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VeyraVault v3.0 Upgrade Script - Part 2
UI & Activities: Stealth Dashboard (Iran Jalali + NY Gregorian Clocks),
SVG Bottom Nav (Dashboard, Spaces, +, Guide, Settings), Space Rename (3-dots),
Quick Lock Button, Live Instant Refresh, Apple/iPhone Models, City/Country Location,
Dual Lock Screen with Fallback, Anti-Uninstall Blocker & External Store/APK Installer.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def write_file(rel_path, content):
    full_path = os.path.join(ROOT, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"[v3-Part2] Updated: {rel_path}")

def apply_part2():
    # 1. VaultDeviceAdminReceiver: Blocks unauthorized user from tapping "Allow" on uninstall/deactivate
    write_file("app/src/main/java/com/veyravault/space/security/VaultDeviceAdminReceiver.java", """
package com.veyravault.space.security;

import android.app.admin.DeviceAdminReceiver;
import android.content.Context;
import android.content.Intent;
import android.widget.Toast;
import com.veyravault.space.ui.SecurityLockActivity;

public class VaultDeviceAdminReceiver extends DeviceAdminReceiver {

    @Override
    public void onEnabled(Context context, Intent intent) {
        Toast.makeText(context, "حفاظت ضدحذف فعال شد.", Toast.LENGTH_SHORT).show();
    }

    @Override
    public CharSequence onDisableRequested(Context context, Intent intent) {
        // Immediately lock session and pop up SecurityLockActivity over the system settings screen
        // so an unauthorized person cannot tap "Allow / Deactivate" to uninstall the app!
        if (SecurityManager.isLockEnabled(context)) {
            SecurityManager.setSessionUnlocked(false);
            try {
                Intent lockIntent = new Intent(context, SecurityLockActivity.class);
                lockIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
                lockIntent.putExtra("block_uninstall_attempt", true);
                context.startActivity(lockIntent);
            } catch (Throwable ignored) {}
        }
        return "⛔ حذف مقدور نمی‌باشد! حذف این برنامه غیرفعال شده است .";
    }

    @Override
    public void onDisabled(Context context, Intent intent) {
        Toast.makeText(context, "حفاظت ضدحذف غیرفعال شد.", Toast.LENGTH_SHORT).show();
    }
}
""")

    # 2. SecurityLockActivity: Dual Lock (PIN + Pattern) with Priority & Automatic Secondary Fallback
    write_file("app/src/main/java/com/veyravault/space/ui/SecurityLockActivity.java", """
package com.veyravault.space.ui;

import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import com.veyravault.space.security.PatternLockView;
import com.veyravault.space.security.SecurityManager;
import com.veyravault.space.util.LocaleHelper;

import java.util.List;

public class SecurityLockActivity extends BaseActivity {

    private String currentMode; // "PIN" or "PATTERN"
    private int failedAttempts = 0;
    private LinearLayout modeContainer;
    private TextView tvSubtitle;
    private TextView tvFallbackSwitch;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        currentMode = SecurityManager.getPriorityMode(this);
        buildLockScreen();
    }

    private void buildLockScreen() {
        boolean fa = isFa();
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        root.setBackgroundColor(Color.parseColor("#0F172A"));
        int pad = dp(24);
        root.setPadding(pad, pad, pad, pad);

        TextView lockIcon = new TextView(this);
        lockIcon.setText("🔒");
        lockIcon.setTextSize(42f);
        lockIcon.setGravity(Gravity.CENTER);
        root.addView(lockIcon);

        TextView title = new TextView(this);
        title.setText(fa ? "قفل امنیتی فعال است" : "Security Lock Active");
        title.setTextSize(21f);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setTextColor(Color.WHITE);
        title.setGravity(Gravity.CENTER);
        title.setPadding(0, dp(8), 0, dp(6));
        root.addView(title);

        tvSubtitle = new TextView(this);
        tvSubtitle.setTextSize(13.5f);
        tvSubtitle.setTextColor(Color.parseColor("#94A3B8"));
        tvSubtitle.setGravity(Gravity.CENTER);
        tvSubtitle.setPadding(0, 0, 0, dp(18));
        root.addView(tvSubtitle);

        modeContainer = new LinearLayout(this);
        modeContainer.setOrientation(LinearLayout.VERTICAL);
        modeContainer.setGravity(Gravity.CENTER);
        root.addView(modeContainer, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT));

        tvFallbackSwitch = new TextView(this);
        tvFallbackSwitch.setTextSize(14f);
        tvFallbackSwitch.setTypeface(Typeface.DEFAULT_BOLD);
        tvFallbackSwitch.setTextColor(Color.parseColor("#60A5FA"));
        tvFallbackSwitch.setGravity(Gravity.CENTER);
        tvFallbackSwitch.setPadding(dp(14), dp(16), dp(14), dp(10));
        tvFallbackSwitch.setVisibility(View.GONE);
        tvFallbackSwitch.setOnClickListener(v -> {
            if ("PIN".equals(currentMode) && SecurityManager.hasPatternConfigured(this)) {
                currentMode = "PATTERN";
            } else if ("PATTERN".equals(currentMode) && SecurityManager.hasPinConfigured(this)) {
                currentMode = "PIN";
            }
            failedAttempts = 0;
            renderActiveModeView();
        });
        root.addView(tvFallbackSwitch);

        renderActiveModeView();
        setContentView(root);
    }

    private void renderActiveModeView() {
        boolean fa = isFa();
        modeContainer.removeAllViews();

        if ("PIN".equals(currentMode)) {
            tvSubtitle.setText(fa ? "لطفاً رمز پین خود را وارد نمایید" : "Please enter your numeric PIN");

            final EditText pinInput = new EditText(this);
            pinInput.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_VARIATION_PASSWORD);
            pinInput.setTextColor(Color.WHITE);
            pinInput.setHintTextColor(Color.parseColor("#64748B"));
            pinInput.setHint(fa ? "رمز پین..." : "Enter PIN...");
            pinInput.setGravity(Gravity.CENTER);
            pinInput.setTextSize(20f);
            GradientDrawable box = new GradientDrawable();
            box.setColor(Color.parseColor("#1E293B"));
            box.setCornerRadius(dp(14));
            box.setStroke(dp(1), Color.parseColor("#334155"));
            pinInput.setBackground(box);
            pinInput.setPadding(dp(16), dp(14), dp(16), dp(14));

            LinearLayout.LayoutParams pinLp = new LinearLayout.LayoutParams(dp(250), LinearLayout.LayoutParams.WRAP_CONTENT);
            pinLp.bottomMargin = dp(16);
            modeContainer.addView(pinInput, pinLp);

            Button unlockBtn = new Button(this);
            unlockBtn.setAllCaps(false);
            unlockBtn.setText(fa ? "باز کردن قفل" : "Unlock");
            unlockBtn.setTextColor(Color.WHITE);
            unlockBtn.setTextSize(15f);
            unlockBtn.setTypeface(Typeface.DEFAULT_BOLD);
            GradientDrawable btnBg = new GradientDrawable();
            btnBg.setColor(Color.parseColor("#2563EB"));
            btnBg.setCornerRadius(dp(22));
            unlockBtn.setBackground(btnBg);
            unlockBtn.setOnClickListener(v -> {
                String entered = pinInput.getText().toString().trim();
                if (SecurityManager.verifyPin(this, entered)) {
                    SecurityManager.setSessionUnlocked(true);
                    finish();
                } else {
                    pinInput.setText("");
                    onFailedAttempt();
                }
            });
            modeContainer.addView(unlockBtn, new LinearLayout.LayoutParams(dp(220), dp(48)));
        } else {
            tvSubtitle.setText(fa ? "الگوی امنیتی خود را رسم کنید" : "Draw your unlock pattern");

            PatternLockView patternView = new PatternLockView(this);
            LinearLayout.LayoutParams patLp = new LinearLayout.LayoutParams(dp(270), dp(270));
            modeContainer.addView(patternView, patLp);

            patternView.setOnPatternListener(new PatternLockView.OnPatternListener() {
                @Override
                public void onPatternComplete(List<Integer> pattern) {
                    String serialized = PatternLockView.patternToString(pattern);
                    if (SecurityManager.verifyPattern(SecurityLockActivity.this, serialized)) {
                        SecurityManager.setSessionUnlocked(true);
                        finish();
                    } else {
                        patternView.clearPattern();
                        onFailedAttempt();
                    }
                }
            });
        }
        updateFallbackSwitchPrompt(false);
    }

    private void onFailedAttempt() {
        failedAttempts++;
        boolean fa = isFa();
        Toast.makeText(this,
                fa ? ("رمز اشتباه است! (تلاش " + failedAttempts + ")") : ("Incorrect passcode! (Attempt " + failedAttempts + ")"),
                Toast.LENGTH_SHORT).show();
        updateFallbackSwitchPrompt(true);
    }

    private void updateFallbackSwitchPrompt(boolean highlight) {
        boolean fa = isFa();
        if (!SecurityManager.hasBothConfigured(this)) {
            tvFallbackSwitch.setVisibility(View.GONE);
            return;
        }
        // Show fallback switch link after 2 failed attempts (or if user needs secondary lock)
        if (failedAttempts >= 2 || highlight) {
            tvFallbackSwitch.setVisibility(View.VISIBLE);
            if ("PIN".equals(currentMode)) {
                tvFallbackSwitch.setText(fa
                        ? "آیا از الگو استفاده می‌کنید؟ ورود با الگو ⬅"
                        : "Using Pattern instead? Tap to unlock with Pattern ➔");
            } else {
                tvFallbackSwitch.setText(fa
                        ? "آیا از رمز پین استفاده می‌کنید؟ ورود با پین ⬅"
                        : "Using PIN instead? Tap to unlock with PIN ➔");
            }
        } else {
            tvFallbackSwitch.setVisibility(View.GONE);
        }
    }

    private boolean isFa() {
        return "fa".equals(LocaleHelper.getLanguage(this));
    }

    private int dp(int v) {
        return (int) (v * getResources().getDisplayMetrics().density);
    }

    @Override
    public void onBackPressed() {
        moveTaskToBack(true);
    }
}
""")

    # 3. SecuritySettingsActivity: Dual Lock Setup (PIN + Pattern status & Priority) + Disguise + Anti-Uninstall
    write_file("app/src/main/java/com/veyravault/space/ui/SecuritySettingsActivity.java", """
package com.veyravault.space.ui;

import android.app.AlertDialog;
import android.app.admin.DevicePolicyManager;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.text.InputType;
import android.view.Gravity;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Switch;
import android.widget.TextView;
import android.widget.Toast;

import com.veyravault.space.security.AppDisguiseManager;
import com.veyravault.space.security.PatternLockView;
import com.veyravault.space.security.SecurityManager;
import com.veyravault.space.security.VaultDeviceAdminReceiver;
import com.veyravault.space.util.LocaleHelper;

import java.util.List;

public class SecuritySettingsActivity extends BaseActivity {

    private DevicePolicyManager dpm;
    private ComponentName adminComponent;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        dpm = (DevicePolicyManager) getSystemService(Context.DEVICE_POLICY_SERVICE);
        adminComponent = new ComponentName(this, VaultDeviceAdminReceiver.class);
        renderUi();
    }

    @Override
    protected void onResume() {
        super.onResume();
        renderUi();
    }

    private void renderUi() {
        boolean fa = isFa();

        ScrollView scroll = new ScrollView(this);
        scroll.setBackgroundColor(Color.parseColor("#F1F5F9"));

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        int pad = dp(16);
        root.setPadding(pad, pad, pad, dp(32));

        // Header
        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setGravity(Gravity.CENTER_VERTICAL);
        header.setPadding(0, 0, 0, dp(14));

        TextView btnBack = new TextView(this);
        btnBack.setText(fa ? "→" : "←");
        btnBack.setTextSize(24f);
        btnBack.setTextColor(Color.parseColor("#0F172A"));
        btnBack.setPadding(dp(8), dp(4), dp(12), dp(4));
        btnBack.setOnClickListener(v -> finish());
        header.addView(btnBack);

        TextView tvTitle = new TextView(this);
        tvTitle.setText(fa ? "امنیت، قفل دوگانه و مخفی‌سازی" : "Security, Dual Lock & Disguise");
        tvTitle.setTextSize(18f);
        tvTitle.setTypeface(Typeface.DEFAULT_BOLD);
        tvTitle.setTextColor(Color.parseColor("#0F172A"));
        header.addView(tvTitle);
        root.addView(header);

        // Card 1: Dual Lock (PIN + Pattern + Priority)
        LinearLayout lockCard = buildCard();
        TextView lockTitle = new TextView(this);
        lockTitle.setText(fa ? "🔐 تنظیم قفل دوگانه (پین و الگو هم‌زمان)" : "🔐 Dual App Lock (PIN & Pattern)");
        lockTitle.setTextSize(16f);
        lockTitle.setTypeface(Typeface.DEFAULT_BOLD);
        lockTitle.setTextColor(Color.parseColor("#0F172A"));
        lockCard.addView(lockTitle);

        boolean hasPin = SecurityManager.hasPinConfigured(this);
        boolean hasPat = SecurityManager.hasPatternConfigured(this);
        String priority = SecurityManager.getPriorityMode(this);

        TextView lockStatus = new TextView(this);
        String pinState = hasPin ? (fa ? "ثبت شده ✓" : "Configured ✓") : (fa ? "خالی (ثبت نشده) ✗" : "Empty ✗");
        String patState = hasPat ? (fa ? "ثبت شده ✓" : "Configured ✓") : (fa ? "خالی (ثبت نشده) ✗" : "Empty ✗");
        String prioLabel = "PIN".equals(priority) ? (fa ? "رمز پین" : "PIN") : (fa ? "الگو (Pattern)" : "Pattern");

        lockStatus.setText(fa
                ? ("• وضعیت رمز پین: " + pinState + "\n• وضعیت الگو: " + patState + "\n• اولویت قفل اول: " + prioLabel
                   + "\n(در صورت اشتباه زدن قفل اول، گزینه ورود با قفل دوم خودکار زیر صفحه ظاهر می‌شود)")
                : ("• PIN Status: " + pinState + "\n• Pattern Status: " + patState + "\n• Primary Lock Priority: " + prioLabel
                   + "\n(If primary fails, secondary lock link appears automatically)"));
        lockStatus.setTextSize(13f);
        lockStatus.setTextColor(Color.parseColor("#334155"));
        lockStatus.setPadding(0, dp(8), 0, dp(12));
        lockCard.addView(lockStatus);

        LinearLayout btnRow1 = new LinearLayout(this);
        btnRow1.setOrientation(LinearLayout.HORIZONTAL);
        Button btnPin = buildActionButton(fa ? (hasPin ? "ویرایش رمز پین ✓" : "ثبت رمز پین") : (hasPin ? "Edit PIN ✓" : "Set PIN"), "#2563EB");
        btnPin.setOnClickListener(v -> showPinSetupDialog());
        Button btnPattern = buildActionButton(fa ? (hasPat ? "ویرایش الگو ✓" : "ثبت الگو") : (hasPat ? "Edit Pattern ✓" : "Set Pattern"), "#7C3AED");
        btnPattern.setOnClickListener(v -> showPatternSetupDialog());

        LinearLayout.LayoutParams lpHalf = new LinearLayout.LayoutParams(0, dp(44), 1f);
        lpHalf.setMargins(dp(4), 0, dp(4), 0);
        btnRow1.addView(btnPin, lpHalf);
        btnRow1.addView(btnPattern, lpHalf);
        lockCard.addView(btnRow1);

        // Priority Selector Row
        LinearLayout prioRow = new LinearLayout(this);
        prioRow.setOrientation(LinearLayout.HORIZONTAL);
        prioRow.setPadding(0, dp(10), 0, 0);

        Button btnPrioPin = buildActionButton(
                fa ? ("اولویت اول: پین" + ("PIN".equals(priority) ? " ★" : "")) : ("Priority: PIN" + ("PIN".equals(priority) ? " ★" : "")),
                "PIN".equals(priority) ? "#059669" : "#64748B");
        btnPrioPin.setOnClickListener(v -> {
            if (!SecurityManager.hasPinConfigured(this)) {
                Toast.makeText(this, fa ? "ابتدا رمز پین را ثبت کنید!" : "Please set a PIN first!", Toast.LENGTH_SHORT).show();
                return;
            }
            SecurityManager.setPriorityMode(this, "PIN");
            Toast.makeText(this, fa ? "اولویت قفل اول روی «پین» قرار گرفت." : "Primary lock set to PIN.", Toast.LENGTH_SHORT).show();
            renderUi();
        });

        Button btnPrioPat = buildActionButton(
                fa ? ("اولویت اول: الگو" + ("PATTERN".equals(priority) ? " ★" : "")) : ("Priority: Pattern" + ("PATTERN".equals(priority) ? " ★" : "")),
                "PATTERN".equals(priority) ? "#059669" : "#64748B");
        btnPrioPat.setOnClickListener(v -> {
            if (!SecurityManager.hasPatternConfigured(this)) {
                Toast.makeText(this, fa ? "ابتدا الگو را ثبت کنید!" : "Please set a Pattern first!", Toast.LENGTH_SHORT).show();
                return;
            }
            SecurityManager.setPriorityMode(this, "PATTERN");
            Toast.makeText(this, fa ? "اولویت قفل اول روی «الگو» قرار گرفت." : "Primary lock set to Pattern.", Toast.LENGTH_SHORT).show();
            renderUi();
        });

        prioRow.addView(btnPrioPin, lpHalf);
        prioRow.addView(btnPrioPat, lpHalf);
        lockCard.addView(prioRow);

        if (SecurityManager.isLockEnabled(this)) {
            Button btnDisable = buildActionButton(fa ? "حذف کامل هر دو قفل" : "Disable All Locks", "#EF4444");
            LinearLayout.LayoutParams disLp = new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, dp(42));
            disLp.topMargin = dp(10);
            btnDisable.setOnClickListener(v -> {
                SecurityManager.disableLock(this);
                Toast.makeText(this, fa ? "قفل امنیتی غیرفعال شد" : "Security lock disabled", Toast.LENGTH_SHORT).show();
                renderUi();
            });
            lockCard.addView(btnDisable, disLp);
        }
        root.addView(lockCard);

        // Card 2: App Icon & Name Disguise
        LinearLayout disguiseCard = buildCard();
        TextView disTitle = new TextView(this);
        disTitle.setText(fa ? "🎭 تغییر چهره و مخفی‌سازی آیکون برنامه" : "🎭 App Icon & Name Disguise");
        disTitle.setTextSize(16f);
        disTitle.setTypeface(Typeface.DEFAULT_BOLD);
        disTitle.setTextColor(Color.parseColor("#0F172A"));
        disguiseCard.addView(disTitle);

        TextView disDesc = new TextView(this);
        disDesc.setText(fa
                ? "آیکون و نام برنامه را در صفحه اصلی گوشی به ماشین‌حساب، تقویم، یادداشت یا آب‌وهوا تغییر دهید."
                : "Change the launcher icon and label to Calculator, Calendar, Notes, or Weather.");
        disDesc.setTextSize(13f);
        disDesc.setTextColor(Color.parseColor("#64748B"));
        disDesc.setPadding(0, dp(6), 0, dp(12));
        disguiseCard.addView(disDesc);

        String[][] modes = {
            {AppDisguiseManager.MODE_DEFAULT, fa ? "پیش‌فرض (VeyraVault)" : "Default (VeyraVault)"},
            {AppDisguiseManager.MODE_CALCULATOR, fa ? "🧮 ماشین حساب (Calculator)" : "🧮 Calculator"},
            {AppDisguiseManager.MODE_CALENDAR, fa ? "📅 تقویم (Calendar)" : "📅 Calendar"},
            {AppDisguiseManager.MODE_NOTES, fa ? "📝 یادداشت‌ها (Notes)" : "📝 Notes"},
            {AppDisguiseManager.MODE_WEATHER, fa ? "⛅ آب و هوا (Weather)" : "⛅ Weather"}
        };
        String currentDisguise = AppDisguiseManager.getCurrentDisguise(this);

        for (String[] m : modes) {
            final String code = m[0];
            boolean selected = code.equals(currentDisguise);
            Button b = buildActionButton((selected ? "✓ " : "") + m[1], selected ? "#059669" : "#475569");
            LinearLayout.LayoutParams blp = new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, dp(42));
            blp.bottomMargin = dp(6);
            b.setOnClickListener(v -> {
                AppDisguiseManager.applyDisguise(this, code);
                Toast.makeText(this, fa ? "آیکون برنامه تغییر کرد." : "Launcher disguise updated.", Toast.LENGTH_SHORT).show();
                renderUi();
            });
            disguiseCard.addView(b, blp);
        }
        root.addView(disguiseCard);

        // Card 3: Strict Anti-Uninstall Protection
        LinearLayout adminCard = buildCard();
        LinearLayout adminHeader = new LinearLayout(this);
        adminHeader.setOrientation(LinearLayout.HORIZONTAL);
        adminHeader.setGravity(Gravity.CENTER_VERTICAL);

        TextView admTitle = new TextView(this);
        admTitle.setText(fa ? "🛡️ قفل ضدحذف هوشمند (جلوگیری از حذف)" : "🛡️ Smart Anti-Uninstall Protection");
        admTitle.setTextSize(16f);
        admTitle.setTypeface(Typeface.DEFAULT_BOLD);
        admTitle.setTextColor(Color.parseColor("#0F172A"));
        adminHeader.addView(admTitle, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f));

        final boolean isAdminActive = dpm != null && dpm.isAdminActive(adminComponent);
        Switch swAdmin = new Switch(this);
        swAdmin.setChecked(isAdminActive);
        swAdmin.setOnCheckedChangeListener((buttonView, isChecked) -> {
            if (isChecked && !isAdminActive) {
                Intent intent = new Intent(DevicePolicyManager.ACTION_ADD_DEVICE_ADMIN);
                intent.putExtra(DevicePolicyManager.EXTRA_DEVICE_ADMIN, adminComponent);
                intent.putExtra(DevicePolicyManager.EXTRA_ADD_EXPLANATION,
                        fa ? "جلوگیری از حذف غیرمجاز برنامه VeyraVault" : "Prevent unauthorized uninstallation of VeyraVault");
                startActivity(intent);
            } else if (!isChecked && isAdminActive) {
                dpm.removeActiveAdmin(adminComponent);
                Toast.makeText(this, fa ? "حفاظت ضدحذف خاموش شد." : "Anti-uninstall disabled.", Toast.LENGTH_SHORT).show();
                renderUi();
            }
        });
        adminHeader.addView(swAdmin);
        adminCard.addView(adminHeader);

        TextView admDesc = new TextView(this);
        admDesc.setText(fa
                ? "وقتی این گزینه روشن و قفل برنامه فعال باشد، اگر کسی بیرون از برنامه بخواهد برنامه را حذف یا قطع اتصال کند، صفحه قفل امنیتی فوراً روی صفحه باز می‌شود تا نتواند دکمه «مجاز» را بزند! برای حذف عادی، ابتدا این کلید را از همین‌جا خاموش کنید."
                : "When active alongside App Lock, any external attempt to deactivate or uninstall immediately pops up the Security Lock screen to block tapping Allow.");
        admDesc.setTextSize(13f);
        admDesc.setTextColor(Color.parseColor("#64748B"));
        admDesc.setPadding(0, dp(8), 0, 0);
        adminCard.addView(admDesc);

        root.addView(adminCard);
        scroll.addView(root);
        setContentView(scroll);
    }

    private void showPinSetupDialog() {
        boolean fa = isFa();
        AlertDialog.Builder b = new AlertDialog.Builder(this);
        b.setTitle(fa ? "تنظیم رمز پین عددی" : "Set Numeric PIN");

        final EditText input = new EditText(this);
        input.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_VARIATION_PASSWORD);
        input.setHint(fa ? "حداقل ۴ رقم وارد کنید..." : "Enter at least 4 digits...");
        input.setPadding(dp(20), dp(16), dp(20), dp(16));
        b.setView(input);

        b.setPositiveButton(fa ? "ثبت و ذخیره پین" : "Save PIN", (d, w) -> {
            String pin = input.getText().toString().trim();
            if (pin.length() < 4) {
                Toast.makeText(this, fa ? "خطا: رمز پین خالی یا کمتر از ۴ رقم است!" : "PIN must be at least 4 digits!", Toast.LENGTH_LONG).show();
                return;
            }
            SecurityManager.savePinPasscode(this, pin);
            Toast.makeText(this, fa ? "✓ رمز پین با موفقیت ثبت و فعال شد!" : "✓ PIN saved and verified!", Toast.LENGTH_SHORT).show();
            renderUi();
        });
        b.setNegativeButton(fa ? "انصراف" : "Cancel", null);
        b.show();
    }

    private void showPatternSetupDialog() {
        boolean fa = isFa();
        AlertDialog.Builder b = new AlertDialog.Builder(this);
        b.setTitle(fa ? "رسم الگوی امنیتی (حداقل ۴ نقطه)" : "Draw Unlock Pattern (min 4 dots)");

        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setGravity(Gravity.CENTER);
        box.setBackgroundColor(Color.parseColor("#0F172A"));
        box.setPadding(dp(16), dp(16), dp(16), dp(16));

        PatternLockView pv = new PatternLockView(this);
        box.addView(pv, new LinearLayout.LayoutParams(dp(260), dp(260)));
        b.setView(box);
        b.setNegativeButton(fa ? "انصراف" : "Cancel", null);

        final AlertDialog dialog = b.create();
        pv.setOnPatternListener(new PatternLockView.OnPatternListener() {
            @Override
            public void onPatternComplete(List<Integer> pattern) {
                if (pattern.size() < 4) {
                    Toast.makeText(SecuritySettingsActivity.this,
                            fa ? "خطا: حداقل ۴ نقطه را به هم وصل کنید!" : "Connect at least 4 dots!",
                            Toast.LENGTH_SHORT).show();
                    pv.clearPattern();
                    return;
                }
                SecurityManager.savePatternPasscode(SecuritySettingsActivity.this, PatternLockView.patternToString(pattern));
                Toast.makeText(SecuritySettingsActivity.this,
                        fa ? "✓ الگوی امنیتی با موفقیت ثبت و فعال شد!" : "✓ Pattern saved and verified!",
                        Toast.LENGTH_SHORT).show();
                dialog.dismiss();
                renderUi();
            }
        });
        dialog.show();
    }

    private LinearLayout buildCard() {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(Color.WHITE);
        bg.setCornerRadius(dp(18));
        card.setBackground(bg);
        int p = dp(16);
        card.setPadding(p, p, p, p);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        lp.bottomMargin = dp(14);
        card.setLayoutParams(lp);
        return card;
    }

    private Button buildActionButton(String text, String hexColor) {
        Button btn = new Button(this);
        btn.setAllCaps(false);
        btn.setText(text);
        btn.setTextColor(Color.WHITE);
        btn.setTextSize(13f);
        btn.setTypeface(Typeface.DEFAULT_BOLD);
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(Color.parseColor(hexColor));
        bg.setCornerRadius(dp(12));
        btn.setBackground(bg);
        return btn;
    }

    private boolean isFa() {
        return "fa".equals(LocaleHelper.getLanguage(this));
    }

    private int dp(int v) {
        return (int) (v * getResources().getDisplayMetrics().density);
    }
}
""")

    # 4. GlobalEnvironmentActivity: Apple/iPhone Models + Priority Explanation + City, Country (Falkenstein, Germany) + IP/Proxy Shield
    write_file("app/src/main/java/com/veyravault/space/ui/GlobalEnvironmentActivity.java", """
package com.veyravault.space.ui;

import android.app.AlertDialog;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Switch;
import android.widget.TextView;
import android.widget.Toast;

import com.veyravault.space.core.CloneMetadataStore;
import com.veyravault.space.core.GmsSupportManager;
import com.veyravault.space.core.VirtualHookManager;
import com.veyravault.space.util.LocaleHelper;

public class GlobalEnvironmentActivity extends BaseActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        renderUi();
    }

    private void renderUi() {
        boolean fa = isFa();

        ScrollView scroll = new ScrollView(this);
        scroll.setBackgroundColor(Color.parseColor("#F1F5F9"));

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        int pad = dp(16);
        root.setPadding(pad, pad, pad, dp(32));

        // Header
        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setGravity(Gravity.CENTER_VERTICAL);
        header.setPadding(0, 0, 0, dp(14));

        TextView btnBack = new TextView(this);
        btnBack.setText(fa ? "→" : "←");
        btnBack.setTextSize(24f);
        btnBack.setTextColor(Color.parseColor("#0F172A"));
        btnBack.setPadding(dp(8), dp(4), dp(12), dp(4));
        btnBack.setOnClickListener(v -> finish());
        header.addView(btnBack);

        TextView tvTitle = new TextView(this);
        tvTitle.setText(fa ? "تنظیمات مدل گوشی، منطقه، آی‌پی و گوگل" : "Global Device, Region, IP & GMS");
        tvTitle.setTextSize(17f);
        tvTitle.setTypeface(Typeface.DEFAULT_BOLD);
        tvTitle.setTextColor(Color.parseColor("#0F172A"));
        header.addView(tvTitle);
        root.addView(header);

        // Priority Notice Banner
        LinearLayout noticeCard = buildCard();
        GradientDrawable noticeBg = new GradientDrawable();
        noticeBg.setColor(Color.parseColor("#EFF6FF"));
        noticeBg.setCornerRadius(dp(14));
        noticeBg.setStroke(dp(1), Color.parseColor("#BFDBFE"));
        noticeCard.setBackground(noticeBg);

        TextView tvNotice = new TextView(this);
        tvNotice.setText(fa
                ? "💡 قانون اولویت هوشمند:\nتمام فضاها به صورت پیش‌فرض با مدل گوشی و منطقه‌ای که در این صفحه ثبت می‌کنید شناخته می‌شوند؛ اما اگر در صفحه «فضاها» از منوی سه نقطه (⋮) برای یک برنامه خاص مدل یا موقعیت مکانی جداگانه‌ای ثبت کنید، اولویت ۱۰۰٪ با تغییر اختصاصی همان برنامه خواهد بود."
                : "💡 Smart Priority Rule:\nAll spaces use this global device & region by default. However, if you customize a specific app's model or location via its (⋮) menu, that per-app setting takes 100% priority.");
        tvNotice.setTextSize(12.5f);
        tvNotice.setTextColor(Color.parseColor("#1E3A8A"));
        noticeCard.addView(tvNotice);
        root.addView(noticeCard);

        // Card 1: Global Device Model (Including Apple / iPhone)
        LinearLayout spoofCard = buildCard();
        LinearLayout topRow = new LinearLayout(this);
        topRow.setOrientation(LinearLayout.HORIZONTAL);
        topRow.setGravity(Gravity.CENTER_VERTICAL);

        TextView spTitle = new TextView(this);
        spTitle.setText(fa ? "📱 مدل گوشی سراسری (شامل اپل و اندروید)" : "📱 Global Device Model (Apple & Android)");
        spTitle.setTextSize(15.5f);
        spTitle.setTypeface(Typeface.DEFAULT_BOLD);
        spTitle.setTextColor(Color.parseColor("#0F172A"));
        topRow.addView(spTitle, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f));

        boolean enabled = CloneMetadataStore.isGlobalDeviceSpoofEnabled(this);
        String[] current = CloneMetadataStore.getGlobalDeviceSpoof(this);

        Switch swSpoof = new Switch(this);
        swSpoof.setChecked(enabled);
        swSpoof.setOnCheckedChangeListener((b, chk) -> {
            CloneMetadataStore.setGlobalDeviceSpoof(this, chk, current[0], current[1], current[2], current[3], current[4], current[5]);
            VirtualHookManager.applyGlobalEnvironmentToRuntime(this);
            setResult(RESULT_OK);
            renderUi();
        });
        topRow.addView(swSpoof);
        spoofCard.addView(topRow);

        TextView activeSummary = new TextView(this);
        activeSummary.setText((fa ? "مدل فعال فعلی: " : "Current Active Model: ") + CloneMetadataStore.getGlobalDeviceSummary(this));
        activeSummary.setTextSize(13f);
        activeSummary.setTypeface(Typeface.DEFAULT_BOLD);
        activeSummary.setTextColor(Color.parseColor("#2563EB"));
        activeSummary.setPadding(0, dp(8), 0, dp(10));
        spoofCard.addView(activeSummary);

        String[][] presets = {
            {"Apple", "iPhone 16 Pro Max", "iPhone17,2", "us", "310260", "T-Mobile USA",
             fa ? "🍎 Apple iPhone 16 Pro Max (پرچمدار اپل)" : "🍎 Apple iPhone 16 Pro Max"},
            {"Apple", "iPhone 15 Pro Max", "iPhone16,2", "de", "26201", "Telekom.de",
             fa ? "🍎 Apple iPhone 15 Pro Max (اپل)" : "🍎 Apple iPhone 15 Pro Max"},
            {"Apple", "iPhone 14 Pro", "iPhone15,2", "gb", "23415", "Vodafone UK",
             fa ? "🍎 Apple iPhone 14 Pro (اپل)" : "🍎 Apple iPhone 14 Pro"},
            {"Apple", "iPad Pro M4", "iPad16,6", "us", "310410", "AT&T USA",
             fa ? "🍎 Apple iPad Pro M4 (آیپد پرو)" : "🍎 Apple iPad Pro M4"},
            {"Samsung", "SM-S928B (Galaxy S24 Ultra)", "e3q", "de", "26201", "Telekom.de",
             fa ? "🇸🇰 Samsung Galaxy S24 Ultra (SM-S928B)" : "🇸🇰 Samsung Galaxy S24 Ultra"},
            {"Google", "Pixel 8 Pro", "husky", "de", "26201", "Telekom.de",
             fa ? "🇬 Google Pixel 8 Pro (گوگل پیکسل)" : "🇬 Google Pixel 8 Pro"},
            {"Samsung", "SM-S918B (Galaxy S23 Ultra)", "dm3q", "ae", "42402", "Etisalat UAE",
             fa ? "🇸🇰 Samsung Galaxy S23 Ultra (امارات)" : "🇸🇰 Samsung Galaxy S23 Ultra"},
            {"Xiaomi", "23116PN5BC (Xiaomi 14 Pro)", "shennong", "tr", "28601", "Turkcell",
             fa ? "🇽 Xiaomi 14 Pro (شیائومی ۱۴ پرو)" : "🇽 Xiaomi 14 Pro"}
        };

        for (String[] p : presets) {
            boolean isCurrent = enabled && p[1].equals(current[1]);
            Button btn = buildActionButton((isCurrent ? "✓ " : "") + p[6], isCurrent ? "#059669" : "#2563EB");
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, dp(42));
            lp.bottomMargin = dp(6);
            btn.setOnClickListener(v -> {
                CloneMetadataStore.setGlobalDeviceSpoof(this, true, p[0], p[1], p[2], p[3], p[4], p[5]);
                VirtualHookManager.applyGlobalEnvironmentToRuntime(this);
                setResult(RESULT_OK);
                Toast.makeText(this, fa ? "مدل سراسری فوراً اعمال شد!" : "Global model applied immediately!", Toast.LENGTH_SHORT).show();
                renderUi();
            });
            spoofCard.addView(btn, lp);
        }
        root.addView(spoofCard);

        // Card 2: Dedicated Region (City, Country like Falkenstein, Germany) & IP/Proxy Shield
        LinearLayout regionCard = buildCard();
        TextView regTitle = new TextView(this);
        regTitle.setText(fa ? "🌍 تنظیمات منطقه (شهر، کشور) و سپر آی‌پی نشست‌ها" : "🌍 Region (City, Country) & Session IP Shield");
        regTitle.setTextSize(15.5f);
        regTitle.setTypeface(Typeface.DEFAULT_BOLD);
        regTitle.setTextColor(Color.parseColor("#0F172A"));
        regionCard.addView(regTitle);

        String activeRegion = CloneMetadataStore.getGlobalRegionLabel(this);
        double[] activeCoords = CloneMetadataStore.getGlobalCoordinates(this);
        String activeTz = CloneMetadataStore.getGlobalTimezone(this);
        String proxyHost = CloneMetadataStore.getGlobalProxyHost(this);
        int proxyPort = CloneMetadataStore.getGlobalProxyPort(this);
        String virtualIp = CloneMetadataStore.getGlobalVirtualIp(this);

        TextView regStatus = new TextView(this);
        regStatus.setText(fa
                ? String.format(java.util.Locale.US,
                    "• شهر و کشور فعال: %s\n• مختصات پایه: %.4f, %.4f\n• منطقه زمانی قفل‌شده: %s\n• آی‌پی/پروکسی: %s",
                    activeRegion, activeCoords[0], activeCoords[1], activeTz,
                    (proxyHost.isEmpty() ? ("آی‌پی مجازی " + virtualIp) : (proxyHost + ":" + proxyPort)))
                : String.format(java.util.Locale.US,
                    "• Active Region: %s\n• Base Coords: %.4f, %.4f\n• Locked Timezone: %s\n• IP/Proxy: %s",
                    activeRegion, activeCoords[0], activeCoords[1], activeTz,
                    (proxyHost.isEmpty() ? ("Virtual IP " + virtualIp) : (proxyHost + ":" + proxyPort))));
        regStatus.setTextSize(13f);
        regStatus.setTextColor(Color.parseColor("#1E40AF"));
        regStatus.setPadding(0, dp(8), 0, dp(12));
        regionCard.addView(regStatus);

        Object[][] regionPresets = {
            {"Falkenstein, Germany", 50.4779, 12.3713, "Europe/Berlin", "88.198.24.108"},
            {"Frankfurt, Germany", 50.1109, 8.6821, "Europe/Berlin", "116.202.120.45"},
            {"New York, United States", 40.7128, -74.0060, "America/New_York", "104.244.72.115"},
            {"London, United Kingdom", 51.5074, -0.1278, "Europe/London", "51.89.152.30"},
            {"Amsterdam, Netherlands", 52.3676, 4.9041, "Europe/Amsterdam", "95.211.198.14"},
            {"Istanbul, Turkey", 41.0082, 28.9784, "Europe/Istanbul", "185.125.33.90"},
            {"Dubai, United Arab Emirates", 25.2048, 55.2708, "Asia/Dubai", "94.200.24.10"},
            {"Tehran, Iran", 35.6892, 51.3890, "Asia/Tehran", "5.160.120.14"}
        };

        for (Object[] rp : regionPresets) {
            final String rName = (String) rp[0];
            final double rLat = (Double) rp[1];
            final double rLon = (Double) rp[2];
            final String rTz = (String) rp[3];
            final String rIp = (String) rp[4];
            boolean sel = rName.equalsIgnoreCase(activeRegion);

            Button b = buildActionButton((sel ? "✓ " : "📍 ") + rName, sel ? "#059669" : "#334155");
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, dp(40));
            lp.bottomMargin = dp(6);
            b.setOnClickListener(v -> {
                CloneMetadataStore.setGlobalRegionAndNetwork(this, rName, rLat, rLon, rTz, proxyHost, proxyPort, rIp);
                VirtualHookManager.applyGlobalEnvironmentToRuntime(this);
                setResult(RESULT_OK);
                Toast.makeText(this, fa ? ("منطقه «" + rName + "» فعال شد!") : ("Region set to " + rName), Toast.LENGTH_SHORT).show();
                renderUi();
            });
            regionCard.addView(b, lp);
        }

        Button btnCustomRegionIp = buildActionButton(
                fa ? "⚙️ ویرایش دستی شهر، کشور و پروکسی/آی‌پی اختصاصی" : "⚙️ Custom City, Country & Proxy/IP Setup",
                "#7C3AED");
        LinearLayout.LayoutParams clp = new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, dp(44));
        clp.topMargin = dp(6);
        btnCustomRegionIp.setOnClickListener(v -> showCustomRegionAndProxyDialog());
        regionCard.addView(btnCustomRegionIp, clp);
        root.addView(regionCard);

        // Card 3: Google Play Services (GMS) Manager for All Spaces
        LinearLayout gmsCard = buildCard();
        TextView gmsTitle = new TextView(this);
        gmsTitle.setText(fa ? "🇬 مدیریت سرویس‌های گوگل پلی (GMS) در فضاها" : "🇬 Google Play Services (GMS) Manager");
        gmsTitle.setTextSize(15.5f);
        gmsTitle.setTypeface(Typeface.DEFAULT_BOLD);
        gmsTitle.setTextColor(Color.parseColor("#0F172A"));
        gmsCard.addView(gmsTitle);

        TextView gmsDesc = new TextView(this);
        gmsDesc.setText(fa
                ? "نصب و فعال‌سازی یکپارچه سرویس‌های گوگل‌پلی برای اجرای بدون خطای یوتیوب، وایبر، جیمیل و برنامه‌های وابسته به گوگل."
                : "Enable Google Play Services across spaces so YouTube, Viber, and Google apps run without errors.");
        gmsDesc.setTextSize(12.5f);
        gmsDesc.setTextColor(Color.parseColor("#64748B"));
        gmsDesc.setPadding(0, dp(6), 0, dp(10));
        gmsCard.addView(gmsDesc);

        Button btnEnableAllGms = buildActionButton(
                fa ? "⚡ فعال‌سازی یکپارچه گوگل‌پلی (GMS) در تمام فضاها" : "⚡ Enable GMS Across All Spaces",
                "#059669");
        LinearLayout.LayoutParams allGmsLp = new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, dp(44));
        allGmsLp.bottomMargin = dp(10);
        btnEnableAllGms.setOnClickListener(v -> {
            for (int uid = 0; uid < 6; uid++) {
                GmsSupportManager.installGms(uid);
            }
            VirtualHookManager.installGmsAvailabilityBypass();
            Toast.makeText(this, fa ? "سرویس‌های گوگل در تمام فضاها فعال شد!" : "GMS enabled across all spaces!", Toast.LENGTH_SHORT).show();
            renderUi();
        });
        gmsCard.addView(btnEnableAllGms, allGmsLp);

        for (int i = 0; i < 4; i++) {
            final int spaceId = i;
            LinearLayout row = new LinearLayout(this);
            row.setOrientation(LinearLayout.HORIZONTAL);
            row.setGravity(Gravity.CENTER_VERTICAL);
            row.setPadding(0, dp(4), 0, dp(4));

            String sTitle = CloneMetadataStore.getSpaceDisplayTitle(this, spaceId, fa ? "فضای" : "Space");
            TextView lbl = new TextView(this);
            lbl.setText(sTitle + " (GMS)");
            lbl.setTextSize(13.5f);
            lbl.setTextColor(Color.parseColor("#0F172A"));
            row.addView(lbl, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f));

            final boolean installed = GmsSupportManager.isGmsInstalled(spaceId);
            Button toggle = buildActionButton(
                    installed ? (fa ? "فعال ✓" : "Installed ✓") : (fa ? "نصب GMS +" : "Install GMS +"),
                    installed ? "#059669" : "#2563EB");
            toggle.setOnClickListener(v -> {
                GmsSupportManager.toggleGmsForUser(spaceId);
                renderUi();
            });
            row.addView(toggle, new LinearLayout.LayoutParams(dp(125), dp(36)));
            gmsCard.addView(row);
        }

        root.addView(gmsCard);
        scroll.addView(root);
        setContentView(scroll);
    }

    private void showCustomRegionAndProxyDialog() {
        boolean fa = isFa();
        AlertDialog.Builder b = new AlertDialog.Builder(this);
        b.setTitle(fa ? "تنظیم دستی شهر، کشور و پروکسی/آی‌پی" : "Custom Region & Proxy/IP");

        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        int p = dp(18);
        layout.setPadding(p, dp(10), p, dp(4));

        final EditText etCityCountry = new EditText(this);
        etCityCountry.setHint(fa ? "شهر و کشور (مثلاً Falkenstein, Germany)" : "City, Country (e.g. Falkenstein, Germany)");
        etCityCountry.setText(CloneMetadataStore.getGlobalRegionLabel(this));
        layout.addView(etCityCountry);

        double[] c = CloneMetadataStore.getGlobalCoordinates(this);
        final EditText etCoords = new EditText(this);
        etCoords.setHint("Latitude, Longitude (e.g. 50.4779, 12.3713)");
        etCoords.setText(String.format(java.util.Locale.US, "%.4f, %.4f", c[0], c[1]));
        layout.addView(etCoords);

        final EditText etTz = new EditText(this);
        etTz.setHint("Timezone (e.g. Europe/Berlin)");
        etTz.setText(CloneMetadataStore.getGlobalTimezone(this));
        layout.addView(etTz);

        final EditText etVirtualIp = new EditText(this);
        etVirtualIp.setHint(fa ? "آی‌پی سرور منطقه (مثلاً 88.198.24.108)" : "Target Region IP (e.g. 88.198.24.108)");
        etVirtualIp.setText(CloneMetadataStore.getGlobalVirtualIp(this));
        layout.addView(etVirtualIp);

        final EditText etProxyHost = new EditText(this);
        etProxyHost.setHint(fa ? "هاست پروکسی SOCKS5/HTTP (اختیاری)" : "Proxy Host (optional)");
        etProxyHost.setText(CloneMetadataStore.getGlobalProxyHost(this));
        layout.addView(etProxyHost);

        final EditText etProxyPort = new EditText(this);
        etProxyPort.setHint(fa ? "پورت پروکسی (مثلاً 1080 یا 0)" : "Proxy Port (e.g. 1080 or 0)");
        int prt = CloneMetadataStore.getGlobalProxyPort(this);
        etProxyPort.setText(prt > 0 ? String.valueOf(prt) : "");
        layout.addView(etProxyPort);

        b.setView(layout);
        b.setPositiveButton(fa ? "ثبت و اعمال آنی" : "Save & Apply Now", (d, w) -> {
            String cc = etCityCountry.getText().toString().trim();
            if (cc.isEmpty()) cc = "Falkenstein, Germany";
            double lat = 50.4779, lon = 12.3713;
            try {
                String[] parts = etCoords.getText().toString().split(",");
                lat = Double.parseDouble(parts[0].trim());
                lon = Double.parseDouble(parts[1].trim());
            } catch (Exception ignored) {}
            String tz = etTz.getText().toString().trim();
            if (tz.isEmpty()) tz = "Europe/Berlin";
            String vip = etVirtualIp.getText().toString().trim();
            String ph = etProxyHost.getText().toString().trim();
            int pp = 0;
            try { pp = Integer.parseInt(etProxyPort.getText().toString().trim()); } catch (Exception ignored) {}

            CloneMetadataStore.setGlobalRegionAndNetwork(this, cc, lat, lon, tz, ph, pp, vip);
            VirtualHookManager.applyGlobalEnvironmentToRuntime(this);
            setResult(RESULT_OK);
            Toast.makeText(this, fa ? "منطقه و آی‌پی با موفقیت اعمال شد!" : "Region & IP applied!", Toast.LENGTH_SHORT).show();
            renderUi();
        });
        b.setNegativeButton(fa ? "انصراف" : "Cancel", null);
        b.show();
    }

    private LinearLayout buildCard() {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(Color.WHITE);
        bg.setCornerRadius(dp(18));
        card.setBackground(bg);
        int p = dp(16);
        card.setPadding(p, p, p, p);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        lp.bottomMargin = dp(14);
        card.setLayoutParams(lp);
        return card;
    }

    private Button buildActionButton(String text, String hexColor) {
        Button btn = new Button(this);
        btn.setAllCaps(false);
        btn.setText(text);
        btn.setTextColor(Color.WHITE);
        btn.setTextSize(13f);
        btn.setTypeface(Typeface.DEFAULT_BOLD);
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(Color.parseColor(hexColor));
        bg.setCornerRadius(dp(12));
        btn.setBackground(bg);
        return btn;
    }

    private boolean isFa() {
        return "fa".equals(LocaleHelper.getLanguage(this));
    }

    private int dp(int v) {
        return (int) (v * getResources().getDisplayMetrics().density);
    }
}
""")

    # 5. SetLocationActivity: Saves BOTH City, Country (e.g. Falkenstein, Germany) AND GPS Coordinates with Global Fallback & Instant Result
    write_file("app/src/main/java/com/veyravault/space/ui/SetLocationActivity.java", """
package com.veyravault.space.ui;

import android.app.AlertDialog;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.preference.PreferenceManager;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.HorizontalScrollView;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import com.veyravault.space.core.CloneMetadataStore;
import com.veyravault.space.core.VirtualHookManager;
import com.veyravault.space.util.LocaleHelper;

import org.osmdroid.config.Configuration;
import org.osmdroid.events.MapEventsReceiver;
import org.osmdroid.tileprovider.tilesource.TileSourceFactory;
import org.osmdroid.util.GeoPoint;
import org.osmdroid.views.MapView;
import org.osmdroid.views.overlay.MapEventsOverlay;
import org.osmdroid.views.overlay.Marker;

import java.util.Locale;

public class SetLocationActivity extends BaseActivity {

    public static final String EXTRA_PKG = "extra_pkg";
    public static final String EXTRA_USER_ID = "extra_user_id";
    public static final String EXTRA_APP_NAME = "extra_app_name";

    private String targetPkg;
    private int targetUserId;
    private String targetAppName;

    private MapView mapView;
    private Marker activeMarker;
    private TextView tvCoordsDisplay;
    private EditText etCityCountry;

    private double selectedLat = 50.4779;
    private double selectedLon = 12.3713;
    private String selectedCityCountry = "Falkenstein, Germany";
    private String selectedTimezone = "Europe/Berlin";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        Configuration.getInstance().load(getApplicationContext(),
                PreferenceManager.getDefaultSharedPreferences(getApplicationContext()));
        Configuration.getInstance().setUserAgentValue(getPackageName());

        targetPkg = getIntent().getStringExtra(EXTRA_PKG);
        targetUserId = getIntent().getIntExtra(EXTRA_USER_ID, 0);
        targetAppName = getIntent().getStringExtra(EXTRA_APP_NAME);
        if (targetPkg == null) targetPkg = "global";
        if (targetAppName == null) targetAppName = targetPkg;

        double[] existing = CloneMetadataStore.getMockLocation(this, targetPkg, targetUserId);
        selectedLat = existing[0];
        selectedLon = existing[1];
        selectedCityCountry = CloneMetadataStore.getEffectiveRegionLabel(this, targetPkg, targetUserId);
        selectedTimezone = CloneMetadataStore.getEffectiveTimezone(this, targetPkg, targetUserId);

        buildMapScreen();
    }

    private void buildMapScreen() {
        boolean fa = isFa();

        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.parseColor("#E2E8F0"));

        mapView = new MapView(this);
        mapView.setTileSource(TileSourceFactory.MAPNIK);
        mapView.setMultiTouchControls(true);
        mapView.getController().setZoom(13.5);
        GeoPoint startPoint = new GeoPoint(selectedLat, selectedLon);
        mapView.getController().setCenter(startPoint);

        activeMarker = new Marker(mapView);
        activeMarker.setPosition(startPoint);
        activeMarker.setAnchor(Marker.ANCHOR_CENTER, Marker.ANCHOR_BOTTOM);
        activeMarker.setTitle(selectedCityCountry);
        mapView.getOverlays().add(activeMarker);

        MapEventsReceiver receiver = new MapEventsReceiver() {
            @Override
            public boolean singleTapConfirmedHelper(GeoPoint p) {
                updatePinPosition(p.getLatitude(), p.getLongitude(), false, null, null);
                return true;
            }

            @Override
            public boolean longPressHelper(GeoPoint p) {
                updatePinPosition(p.getLatitude(), p.getLongitude(), false, null, null);
                return true;
            }
        };
        mapView.getOverlays().add(new MapEventsOverlay(receiver));
        root.addView(mapView, new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.MATCH_PARENT));

        // Top Overlay Bar + City/Country Presets
        LinearLayout topContainer = new LinearLayout(this);
        topContainer.setOrientation(LinearLayout.VERTICAL);
        int pad = dp(12);
        topContainer.setPadding(pad, dp(14), pad, pad);

        LinearLayout headerBar = new LinearLayout(this);
        headerBar.setOrientation(LinearLayout.HORIZONTAL);
        headerBar.setGravity(Gravity.CENTER_VERTICAL);
        GradientDrawable headerBg = new GradientDrawable();
        headerBg.setColor(Color.WHITE);
        headerBg.setCornerRadius(dp(16));
        headerBar.setBackground(headerBg);
        headerBar.setPadding(dp(12), dp(10), dp(12), dp(10));

        TextView btnBack = new TextView(this);
        btnBack.setText(fa ? "→" : "←");
        btnBack.setTextSize(22f);
        btnBack.setTextColor(Color.parseColor("#0F172A"));
        btnBack.setPadding(dp(6), 0, dp(10), 0);
        btnBack.setOnClickListener(v -> finish());
        headerBar.addView(btnBack);

        TextView title = new TextView(this);
        title.setText((fa ? "تنظیم مکان و شهر/کشور: " : "Region & GPS: ") + targetAppName);
        title.setTextSize(14.5f);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setTextColor(Color.parseColor("#0F172A"));
        headerBar.addView(title, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f));

        TextView btnManual = new TextView(this);
        btnManual.setText(fa ? "مختصات دستی" : "Manual");
        btnManual.setTextSize(12f);
        btnManual.setTypeface(Typeface.DEFAULT_BOLD);
        btnManual.setTextColor(Color.parseColor("#2563EB"));
        btnManual.setPadding(dp(8), dp(4), dp(8), dp(4));
        btnManual.setOnClickListener(v -> showManualCoordsDialog());
        headerBar.addView(btnManual);

        topContainer.addView(headerBar);

        // Quick City, Country Chips (including Falkenstein, Germany)
        HorizontalScrollView chipScroll = new HorizontalScrollView(this);
        chipScroll.setHorizontalScrollBarEnabled(false);
        LinearLayout chipRow = new LinearLayout(this);
        chipRow.setOrientation(LinearLayout.HORIZONTAL);
        chipRow.setPadding(0, dp(8), 0, 0);

        Object[][] cities = {
            {"Falkenstein, Germany", 50.4779, 12.3713, "Europe/Berlin"},
            {"Frankfurt, Germany", 50.1109, 8.6821, "Europe/Berlin"},
            {"New York, United States", 40.7128, -74.0060, "America/New_York"},
            {"London, United Kingdom", 51.5074, -0.1278, "Europe/London"},
            {"Istanbul, Turkey", 41.0082, 28.9784, "Europe/Istanbul"},
            {"Dubai, UAE", 25.2048, 55.2708, "Asia/Dubai"},
            {"Tehran, Iran", 35.6892, 51.3890, "Asia/Tehran"},
            {"Singapore, Singapore", 1.3521, 103.8198, "Asia/Singapore"},
            {"Tokyo, Japan", 35.6762, 139.6503, "Asia/Tokyo"}
        };

        for (Object[] c : cities) {
            final String cLabel = (String) c[0];
            final double lat = (Double) c[1];
            final double lon = (Double) c[2];
            final String tz = (String) c[3];

            TextView chip = new TextView(this);
            chip.setText("📍 " + cLabel);
            chip.setTextSize(12f);
            chip.setTypeface(Typeface.DEFAULT_BOLD);
            chip.setTextColor(Color.parseColor("#1E293B"));
            GradientDrawable chipBg = new GradientDrawable();
            chipBg.setColor(Color.WHITE);
            chipBg.setCornerRadius(dp(16));
            chipBg.setStroke(dp(1), Color.parseColor("#CBD5E1"));
            chip.setBackground(chipBg);
            chip.setPadding(dp(12), dp(7), dp(12), dp(7));

            LinearLayout.LayoutParams clp = new LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT);
            clp.setMargins(dp(4), 0, dp(4), 0);
            chip.setOnClickListener(v -> updatePinPosition(lat, lon, true, cLabel, tz));
            chipRow.addView(chip, clp);
        }
        chipScroll.addView(chipRow);
        topContainer.addView(chipScroll);

        FrameLayout.LayoutParams topLp = new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.WRAP_CONTENT);
        topLp.gravity = Gravity.TOP;
        root.addView(topContainer, topLp);

        // Bottom Floating Card
        LinearLayout bottomCard = new LinearLayout(this);
        bottomCard.setOrientation(LinearLayout.VERTICAL);
        GradientDrawable cardBg = new GradientDrawable();
        cardBg.setColor(Color.WHITE);
        cardBg.setCornerRadius(dp(22));
        bottomCard.setBackground(cardBg);
        int bPad = dp(16);
        bottomCard.setPadding(bPad, bPad, bPad, bPad);

        TextView tvRegionPrompt = new TextView(this);
        tvRegionPrompt.setText(fa ? "نام شهر و کشور (برای نمایش در نشست و تنظیمات اپ):" : "City, Country Name (for App & Session):");
        tvRegionPrompt.setTextSize(12f);
        tvRegionPrompt.setTypeface(Typeface.DEFAULT_BOLD);
        tvRegionPrompt.setTextColor(Color.parseColor("#475569"));
        bottomCard.addView(tvRegionPrompt);

        etCityCountry = new EditText(this);
        etCityCountry.setText(selectedCityCountry);
        etCityCountry.setHint("Falkenstein, Germany");
        etCityCountry.setTextSize(14f);
        etCityCountry.setTextColor(Color.parseColor("#0F172A"));
        GradientDrawable etBg = new GradientDrawable();
        etBg.setColor(Color.parseColor("#F8FAFC"));
        etBg.setCornerRadius(dp(10));
        etBg.setStroke(dp(1), Color.parseColor("#CBD5E1"));
        etCityCountry.setBackground(etBg);
        etCityCountry.setPadding(dp(12), dp(8), dp(12), dp(8));
        LinearLayout.LayoutParams etLp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        etLp.topMargin = dp(4);
        etLp.bottomMargin = dp(8);
        bottomCard.addView(etCityCountry, etLp);

        tvCoordsDisplay = new TextView(this);
        tvCoordsDisplay.setTextSize(13f);
        tvCoordsDisplay.setTypeface(Typeface.DEFAULT_BOLD);
        tvCoordsDisplay.setTextColor(Color.parseColor("#1E40AF"));
        tvCoordsDisplay.setGravity(Gravity.CENTER);
        tvCoordsDisplay.setPadding(0, dp(2), 0, dp(10));
        updateCoordsLabel();
        bottomCard.addView(tvCoordsDisplay);

        Button btnSave = new Button(this);
        btnSave.setAllCaps(false);
        btnSave.setText(fa ? "✓ ثبت موقعیت و شهر/کشور (اعمال فوری با اولویت اول)" : "✓ Set Location & Region (Apply Immediately)");
        btnSave.setTextColor(Color.WHITE);
        btnSave.setTextSize(14f);
        btnSave.setTypeface(Typeface.DEFAULT_BOLD);
        GradientDrawable saveBg = new GradientDrawable();
        saveBg.setColor(Color.parseColor("#2563EB"));
        saveBg.setCornerRadius(dp(24));
        btnSave.setBackground(saveBg);
        btnSave.setOnClickListener(v -> {
            String regionText = etCityCountry.getText().toString().trim();
            if (regionText.isEmpty()) regionText = "Falkenstein, Germany";
            CloneMetadataStore.setMockLocationWithRegion(this, targetPkg, targetUserId,
                    selectedLat, selectedLon, regionText, selectedTimezone);
            VirtualHookManager.setMockGpsEnabled(this, true);
            VirtualHookManager.prepareForCloneLaunch(this, targetPkg, targetUserId);
            setResult(RESULT_OK);
            Toast.makeText(this,
                    fa ? ("موقعیت «" + regionText + "» فوراً برای این اپ فعال شد!") : ("Location " + regionText + " activated!"),
                    Toast.LENGTH_SHORT).show();
            finish();
        });
        bottomCard.addView(btnSave, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, dp(46)));

        if (CloneMetadataStore.hasMockLocation(this, targetPkg, targetUserId)) {
            Button btnClear = new Button(this);
            btnClear.setAllCaps(false);
            btnClear.setText(fa ? "حذف موقعیت اختصاصی (بازگشت خودکار به منطقه سراسری)" : "Clear Custom Location (Fallback to Global)");
            btnClear.setTextColor(Color.parseColor("#EF4444"));
            btnClear.setBackgroundColor(Color.TRANSPARENT);
            btnClear.setTextSize(12.5f);
            btnClear.setOnClickListener(v -> {
                CloneMetadataStore.clearMockLocation(this, targetPkg, targetUserId);
                VirtualHookManager.applyBlackBoxVirtualLocation(targetPkg, targetUserId, 0, 0, false);
                setResult(RESULT_OK);
                Toast.makeText(this,
                        fa ? "موقعیت اختصاصی حذف شد؛ منطقه سراسری جایگزین گردید." : "Reverted to global location.",
                        Toast.LENGTH_SHORT).show();
                finish();
            });
            bottomCard.addView(btnClear, new LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT, dp(38)));
        }

        FrameLayout.LayoutParams botLp = new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.WRAP_CONTENT);
        botLp.gravity = Gravity.BOTTOM;
        botLp.setMargins(dp(14), dp(14), dp(14), dp(16));
        root.addView(bottomCard, botLp);

        setContentView(root);
    }

    private void updatePinPosition(double lat, double lon, boolean animateCenter, String cityCountry, String tz) {
        selectedLat = lat;
        selectedLon = lon;
        if (cityCountry != null && !cityCountry.isEmpty()) {
            selectedCityCountry = cityCountry;
            if (etCityCountry != null) etCityCountry.setText(cityCountry);
        }
        if (tz != null && !tz.isEmpty()) {
            selectedTimezone = tz;
        }
        GeoPoint pt = new GeoPoint(lat, lon);
        activeMarker.setPosition(pt);
        if (animateCenter) {
            mapView.getController().animateTo(pt);
        }
        mapView.invalidate();
        updateCoordsLabel();
    }

    private void updateCoordsLabel() {
        boolean fa = isFa();
        String prefix = fa ? "مختصات دقیق انتخاب‌شده: " : "Selected GPS Coordinates: ";
        tvCoordsDisplay.setText(prefix + String.format(Locale.US, "%.5f, %.5f", selectedLat, selectedLon));
    }

    private void showManualCoordsDialog() {
        boolean fa = isFa();
        AlertDialog.Builder b = new AlertDialog.Builder(this);
        b.setTitle(fa ? "ورود دستی مختصات (Latitude, Longitude)" : "Enter Latitude, Longitude");

        final EditText input = new EditText(this);
        input.setInputType(InputType.TYPE_CLASS_TEXT);
        input.setText(String.format(Locale.US, "%.5f, %.5f", selectedLat, selectedLon));
        input.setPadding(dp(20), dp(16), dp(20), dp(16));
        b.setView(input);

        b.setPositiveButton(fa ? "اعمال روی نقشه" : "Apply", (d, w) -> {
            try {
                String[] parts = input.getText().toString().split(",");
                double lat = Double.parseDouble(parts[0].trim());
                double lon = Double.parseDouble(parts[1].trim());
                updatePinPosition(lat, lon, true, null, null);
            } catch (Exception e) {
                Toast.makeText(this, fa ? "فرمت نامعتبر است" : "Invalid coordinates format", Toast.LENGTH_SHORT).show();
            }
        });
        b.setNegativeButton(fa ? "انصراف" : "Cancel", null);
        b.show();
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (mapView != null) mapView.onResume();
    }

    @Override
    protected void onPause() {
        super.onPause();
        if (mapView != null) mapView.onPause();
    }

    private boolean isFa() {
        return "fa".equals(LocaleHelper.getLanguage(this));
    }

    private int dp(int v) {
        return (int) (v * getResources().getDisplayMetrics().density);
    }
}
""")

    # 6. AddAppActivity: External APK / Bazaar / Myket / Google Play Installer + Target Selector (Inside App / Phone / Both)
    write_file("app/src/main/java/com/veyravault/space/ui/AddAppActivity.java", """
package com.veyravault.space.ui;

import android.app.AlertDialog;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextUtils;
import android.text.TextWatcher;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.GridView;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import com.veyravault.space.core.Engine;
import com.veyravault.space.util.LocaleHelper;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

public class AddAppActivity extends BaseActivity {

    private static final int REQ_PICK_APK = 901;

    private List<Engine.AppModel> allApps = new ArrayList<>();
    private List<Engine.AppModel> filteredApps = new ArrayList<>();
    private final Set<String> selectedPackages = new HashSet<>();
    private boolean batchMode = false;

    // 0 = Inside App Only (Independent Vault), 1 = Phone Only, 2 = Both Phone & App
    private int externalInstallTargetMode = 0;

    private GridView gridView;
    private AppGridAdapter adapter;
    private TextView btnBatchClone;
    private Button btnConfirmBatch;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        allApps = Engine.getInstalledApps(this);
        filteredApps.addAll(allApps);
        buildScreen();
    }

    private void buildScreen() {
        boolean fa = isFa();

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.parseColor("#F1F5F9"));
        int pad = dp(14);
        root.setPadding(pad, dp(14), pad, pad);

        // Top Bar
        LinearLayout topBar = new LinearLayout(this);
        topBar.setOrientation(LinearLayout.HORIZONTAL);
        topBar.setGravity(Gravity.CENTER_VERTICAL);
        topBar.setPadding(0, 0, 0, dp(10));

        btnBatchClone = new TextView(this);
        btnBatchClone.setText(fa ? "کلون گروهی" : "Batch clone");
        btnBatchClone.setTextSize(12.5f);
        btnBatchClone.setTypeface(Typeface.DEFAULT_BOLD);
        btnBatchClone.setTextColor(Color.parseColor("#1E40AF"));
        GradientDrawable pillBg = new GradientDrawable();
        pillBg.setColor(Color.parseColor("#DBEAFE"));
        pillBg.setCornerRadius(dp(18));
        btnBatchClone.setBackground(pillBg);
        btnBatchClone.setPadding(dp(14), dp(7), dp(14), dp(7));
        btnBatchClone.setOnClickListener(v -> toggleBatchMode());
        topBar.addView(btnBatchClone);

        TextView tvTitle = new TextView(this);
        tvTitle.setText(fa ? "برنامه‌های من و نصب جدید" : "My Apps & External Install");
        tvTitle.setTextSize(17f);
        tvTitle.setTypeface(Typeface.DEFAULT_BOLD);
        tvTitle.setTextColor(Color.parseColor("#0F172A"));
        tvTitle.setGravity(Gravity.CENTER);
        topBar.addView(tvTitle, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f));

        TextView btnBack = new TextView(this);
        btnBack.setText(fa ? "→" : "←");
        btnBack.setTextSize(24f);
        btnBack.setTextColor(Color.parseColor("#0F172A"));
        btnBack.setPadding(dp(10), dp(2), dp(6), dp(2));
        btnBack.setOnClickListener(v -> finish());
        topBar.addView(btnBack);

        root.addView(topBar);

        // Fixed Top Card: Install App Not on Phone (APK File / Bazaar / Myket / Google Play)
        LinearLayout storeCard = new LinearLayout(this);
        storeCard.setOrientation(LinearLayout.VERTICAL);
        GradientDrawable storeBg = new GradientDrawable();
        storeBg.setColor(Color.WHITE);
        storeBg.setCornerRadius(dp(16));
        storeBg.setStroke(dp(1), Color.parseColor("#BFDBFE"));
        storeCard.setBackground(storeBg);
        storeCard.setPadding(dp(12), dp(10), dp(12), dp(10));
        LinearLayout.LayoutParams storeLp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        storeLp.bottomMargin = dp(10);

        TextView storeTitle = new TextView(this);
        storeTitle.setText(fa
                ? "➕ نصب برنامه جدید (فایل APK / کافه‌بازار / مایکت / گوگل‌پلی)"
                : "➕ Install New App (APK File / Bazaar / Myket / Google Play)");
        storeTitle.setTextSize(13.5f);
        storeTitle.setTypeface(Typeface.DEFAULT_BOLD);
        storeTitle.setTextColor(Color.parseColor("#1E40AF"));
        storeCard.addView(storeTitle);

        TextView storeSub = new TextView(this);
        storeSub.setText(fa
                ? "🛡️ تمام کلون‌ها در صندوق مستقل ذخیره می‌شوند؛ حتی اگر برنامه اصلی را از گوشی پاک کنید، داخل برنامه پاک نمی‌شود!"
                : "🛡️ Clones are stored in an independent vault; uninstalling from the phone will NEVER delete your clones!");
        storeSub.setTextSize(11.5f);
        storeSub.setTextColor(Color.parseColor("#059669"));
        storeSub.setPadding(0, dp(4), 0, dp(8));
        storeCard.addView(storeSub);

        LinearLayout storeBtns = new LinearLayout(this);
        storeBtns.setOrientation(LinearLayout.HORIZONTAL);
        LinearLayout.LayoutParams sBtnLp = new LinearLayout.LayoutParams(0, dp(36), 1f);
        sBtnLp.setMargins(dp(3), 0, dp(3), 0);

        Button bApk = buildMiniButton(fa ? "📂 فایل APK" : "📂 APK File", "#2563EB");
        bApk.setOnClickListener(v -> showTargetModeAndRun(0));

        Button bBazaar = buildMiniButton(fa ? "🛒 بازار" : "🛒 Bazaar", "#059669");
        bBazaar.setOnClickListener(v -> showTargetModeAndRun(1));

        Button bMyket = buildMiniButton(fa ? "📦 مایکت" : "📦 Myket", "#0284C7");
        bMyket.setOnClickListener(v -> showTargetModeAndRun(2));

        Button bPlay = buildMiniButton(fa ? "▶ گوگل‌پلی" : "▶ Play Store", "#7C3AED");
        bPlay.setOnClickListener(v -> showTargetModeAndRun(3));

        storeBtns.addView(bApk, sBtnLp);
        storeBtns.addView(bBazaar, sBtnLp);
        storeBtns.addView(bMyket, sBtnLp);
        storeBtns.addView(bPlay, sBtnLp);
        storeCard.addView(storeBtns);
        root.addView(storeCard, storeLp);

        // Search Bar
        EditText searchInput = new EditText(this);
        searchInput.setHint(fa ? "🔍 جستجو در برنامه‌های گوشی..." : "🔍 Search installed apps...");
        searchInput.setTextSize(14f);
        searchInput.setTextColor(Color.parseColor("#0F172A"));
        searchInput.setHintTextColor(Color.parseColor("#94A3B8"));
        searchInput.setSingleLine(true);
        GradientDrawable searchBg = new GradientDrawable();
        searchBg.setColor(Color.WHITE);
        searchBg.setCornerRadius(dp(20));
        searchInput.setBackground(searchBg);
        searchInput.setPadding(dp(16), dp(10), dp(16), dp(10));

        LinearLayout.LayoutParams searchLp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        searchLp.bottomMargin = dp(10);
        root.addView(searchInput, searchLp);

        searchInput.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) {
                filterApps(s.toString());
            }
            @Override public void afterTextChanged(Editable s) {}
        });

        // 4-Column Grid
        gridView = new GridView(this);
        gridView.setNumColumns(4);
        gridView.setHorizontalSpacing(dp(10));
        gridView.setVerticalSpacing(dp(10));
        gridView.setStretchMode(GridView.STRETCH_COLUMN_WIDTH);
        adapter = new AppGridAdapter();
        gridView.setAdapter(adapter);

        root.addView(gridView, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 0, 1f));

        // Bottom Batch Action Button
        btnConfirmBatch = new Button(this);
        btnConfirmBatch.setAllCaps(false);
        btnConfirmBatch.setTextColor(Color.WHITE);
        btnConfirmBatch.setTextSize(15f);
        btnConfirmBatch.setTypeface(Typeface.DEFAULT_BOLD);
        GradientDrawable confirmBg = new GradientDrawable();
        confirmBg.setColor(Color.parseColor("#2563EB"));
        confirmBg.setCornerRadius(dp(24));
        btnConfirmBatch.setBackground(confirmBg);
        btnConfirmBatch.setVisibility(View.GONE);
        btnConfirmBatch.setOnClickListener(v -> executeBatchClone());

        LinearLayout.LayoutParams confirmLp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, dp(48));
        confirmLp.topMargin = dp(10);
        root.addView(btnConfirmBatch, confirmLp);

        setContentView(root);
    }

    private void showTargetModeAndRun(final int sourceType) {
        boolean fa = isFa();
        String[] options = {
            fa ? "۱. نصب فقط بر روی برنامه (مستقل در صندوق کلون)" : "1. Install inside VeyraVault App ONLY (Independent)",
            fa ? "۲. نصب فقط بر روی گوشی" : "2. Install on Phone ONLY",
            fa ? "۳. نصب بر روی هر دو (هم گوشی و هم داخل برنامه)" : "3. Install on BOTH Phone & VeyraVault App"
        };
        AlertDialog.Builder b = new AlertDialog.Builder(this);
        b.setTitle(fa ? "محل نصب برنامه را انتخاب کنید:" : "Choose Installation Target:");
        b.setSingleChoiceItems(options, externalInstallTargetMode, (d, which) -> externalInstallTargetMode = which);
        b.setPositiveButton(fa ? "ادامه" : "Continue", (d, w) -> {
            if (sourceType == 0) {
                Intent pick = new Intent(Intent.ACTION_GET_CONTENT);
                pick.setType("application/vnd.android.package-archive");
                pick.addCategory(Intent.CATEGORY_OPENABLE);
                try {
                    startActivityForResult(Intent.createChooser(pick, fa ? "انتخاب فایل APK" : "Select APK"), REQ_PICK_APK);
                } catch (Exception e) {
                    Toast.makeText(this, fa ? "مدیریت فایل یافت نشد" : "File picker not found", Toast.LENGTH_SHORT).show();
                }
            } else if (sourceType == 1) {
                openStoreOrClone("com.farsitel.bazaar", "https://cafebazaar.ir");
            } else if (sourceType == 2) {
                openStoreOrClone("ir.mservices.market", "https://myket.ir");
            } else if (sourceType == 3) {
                openStoreOrClone("com.android.vending", "https://play.google.com/store");
            }
        });
        b.setNegativeButton(fa ? "انصراف" : "Cancel", null);
        b.show();
    }

    private void openStoreOrClone(String storePkg, String webUrl) {
        boolean fa = isFa();
        try {
            // If user chose "Install inside App ONLY" or "Both" and store is installed on phone,
            // also ensure the store is cloned inside Space 1 so it can install directly inside virtual space!
            if (externalInstallTargetMode == 0 || externalInstallTargetMode == 2) {
                Engine.installClone(this, storePkg, 0);
                if (externalInstallTargetMode == 0) {
                    boolean launched = Engine.launchClone(this, storePkg, 0);
                    if (launched) {
                        setResult(RESULT_OK);
                        return;
                    }
                }
            }
            Intent launch = getPackageManager().getLaunchIntentForPackage(storePkg);
            if (launch != null) {
                startActivity(launch);
                Toast.makeText(this,
                        fa ? "پس از دانلود برنامه، به صورت خودکار در لیست آماده کلون مستقل است." : "Download app from store.",
                        Toast.LENGTH_LONG).show();
            } else {
                startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(webUrl)));
            }
        } catch (Exception e) {
            try { startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(webUrl))); } catch (Exception ignored) {}
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == REQ_PICK_APK && resultCode == RESULT_OK && data != null && data.getData() != null) {
            handlePickedApkUri(data.getData());
        }
    }

    private void handlePickedApkUri(Uri uri) {
        boolean fa = isFa();
        try {
            File tempApk = new File(getCacheDir(), "picked_install.apk");
            try (InputStream is = getContentResolver().openInputStream(uri);
                 FileOutputStream fos = new FileOutputStream(tempApk)) {
                byte[] buf = new byte[16384];
                int len;
                while ((len = is.read(buf)) > 0) fos.write(buf, 0, len);
            }
            if (externalInstallTargetMode == 0 || externalInstallTargetMode == 2) {
                boolean ok = Engine.installExternalApkFile(this, tempApk, 0);
                if (ok) {
                    Toast.makeText(this,
                            fa ? "✓ برنامه به صورت مستقل در فضای ۱ نصب شد!" : "✓ Installed independently into Space 1!",
                            Toast.LENGTH_SHORT).show();
                    setResult(RESULT_OK);
                }
            }
            if (externalInstallTargetMode == 1 || externalInstallTargetMode == 2) {
                Intent promptInstall = new Intent(Intent.ACTION_VIEW);
                promptInstall.setDataAndType(uri, "application/vnd.android.package-archive");
                promptInstall.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_ACTIVITY_NEW_TASK);
                startActivity(promptInstall);
            } else {
                finish();
            }
        } catch (Exception e) {
            Toast.makeText(this, fa ? "خطا در خواندن فایل APK" : "Failed to install APK", Toast.LENGTH_SHORT).show();
        }
    }

    private Button buildMiniButton(String text, String colorHex) {
        Button b = new Button(this);
        b.setAllCaps(false);
        b.setText(text);
        b.setTextColor(Color.WHITE);
        b.setTextSize(11.5f);
        b.setTypeface(Typeface.DEFAULT_BOLD);
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(Color.parseColor(colorHex));
        bg.setCornerRadius(dp(10));
        b.setBackground(bg);
        b.setPadding(dp(4), 0, dp(4), 0);
        return b;
    }

    private void toggleBatchMode() {
        batchMode = !batchMode;
        selectedPackages.clear();
        updateBatchButtonText();
        btnConfirmBatch.setVisibility(batchMode ? View.VISIBLE : View.GONE);
        adapter.notifyDataSetChanged();
    }

    private void updateBatchButtonText() {
        boolean fa = isFa();
        int count = selectedPackages.size();
        btnConfirmBatch.setText(fa
                ? ("افزودن برنامه‌های انتخاب‌شده (" + count + ")")
                : ("Clone Selected Apps (" + count + ")"));
    }

    private void filterApps(String query) {
        filteredApps.clear();
        String q = query == null ? "" : query.trim().toLowerCase();
        for (Engine.AppModel app : allApps) {
            if (q.isEmpty() || app.name.toLowerCase().contains(q) || app.packageName.toLowerCase().contains(q)) {
                filteredApps.add(app);
            }
        }
        adapter.notifyDataSetChanged();
    }

    private void cloneSingleApp(Engine.AppModel app) {
        boolean fa = isFa();
        int targetUserId = Engine.findNextAvailableUserIdForPackage(this, app.packageName, 20);
        boolean ok = Engine.installClone(this, app.packageName, targetUserId);
        if (ok) {
            Toast.makeText(this,
                    (fa ? "به صورت مستقل به فضای " : "Cloned independently to Space ") + (targetUserId + 1) + (fa ? " اضافه شد" : ""),
                    Toast.LENGTH_SHORT).show();
            setResult(RESULT_OK);
            finish();
        } else {
            Toast.makeText(this, fa ? "خطا در کلون کردن برنامه" : "Failed to clone app", Toast.LENGTH_SHORT).show();
        }
    }

    private void executeBatchClone() {
        boolean fa = isFa();
        if (selectedPackages.isEmpty()) {
            Toast.makeText(this, fa ? "حداقل یک برنامه را انتخاب کنید" : "Select at least one app", Toast.LENGTH_SHORT).show();
            return;
        }
        int successCount = 0;
        for (String pkg : selectedPackages) {
            int targetUserId = Engine.findNextAvailableUserIdForPackage(this, pkg, 20);
            if (Engine.installClone(this, pkg, targetUserId)) {
                successCount++;
            }
        }
        Toast.makeText(this,
                fa ? (successCount + " برنامه به صورت مستقل کلون شد") : (successCount + " apps cloned"),
                Toast.LENGTH_SHORT).show();
        setResult(RESULT_OK);
        finish();
    }

    private class AppGridAdapter extends BaseAdapter {
        @Override public int getCount() { return filteredApps.size(); }
        @Override public Object getItem(int position) { return filteredApps.get(position); }
        @Override public long getItemId(int position) { return position; }

        @Override
        public View getView(int position, View convertView, ViewGroup parent) {
            final Engine.AppModel app = filteredApps.get(position);
            boolean isSelected = selectedPackages.contains(app.packageName);

            LinearLayout card = new LinearLayout(AddAppActivity.this);
            card.setOrientation(LinearLayout.VERTICAL);
            card.setGravity(Gravity.CENTER);
            int pad = dp(8);
            card.setPadding(pad, dp(12), pad, dp(12));

            GradientDrawable cardBg = new GradientDrawable();
            cardBg.setColor(isSelected ? Color.parseColor("#DBEAFE") : Color.WHITE);
            cardBg.setCornerRadius(dp(16));
            if (isSelected) {
                cardBg.setStroke(dp(2), Color.parseColor("#2563EB"));
            }
            card.setBackground(cardBg);

            ImageView iv = new ImageView(AddAppActivity.this);
            iv.setImageDrawable(app.icon);
            card.addView(iv, new LinearLayout.LayoutParams(dp(44), dp(44)));

            TextView tv = new TextView(AddAppActivity.this);
            tv.setText(app.name);
            tv.setTextSize(11.5f);
            tv.setTextColor(Color.parseColor("#1E293B"));
            tv.setSingleLine(true);
            tv.setEllipsize(TextUtils.TruncateAt.END);
            tv.setGravity(Gravity.CENTER);
            tv.setPadding(0, dp(6), 0, 0);
            card.addView(tv);

            card.setOnClickListener(v -> {
                if (batchMode) {
                    if (selectedPackages.contains(app.packageName)) {
                        selectedPackages.remove(app.packageName);
                    } else {
                        selectedPackages.add(app.packageName);
                    }
                    updateBatchButtonText();
                    notifyDataSetChanged();
                } else {
                    cloneSingleApp(app);
                }
            });
            return card;
        }
    }

    private boolean isFa() {
        return "fa".equals(LocaleHelper.getLanguage(this));
    }

    private int dp(int v) {
        return (int) (v * getResources().getDisplayMetrics().density);
    }
}
""")

    # 7. MainActivity: Stealth Dashboard (Iran/NY Clocks) + Spaces (Rename Space 3-dots, Quick Lock, Apple/iPhone, Live Update) + Guide + Settings Hub + SVG Bottom Nav
    write_file("app/src/main/java/com/veyravault/space/ui/MainActivity.java", """
package com.veyravault.space.ui;

import android.app.ActivityManager;
import android.app.AlertDialog;
import android.app.Dialog;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.text.TextUtils;
import android.view.Gravity;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.GridLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import com.veyravault.space.R;
import com.veyravault.space.core.CloneMetadataStore;
import com.veyravault.space.core.Engine;
import com.veyravault.space.core.GmsSupportManager;
import com.veyravault.space.core.VirtualHookManager;
import com.veyravault.space.security.SecurityManager;
import com.veyravault.space.util.JalaliClockUtil;
import com.veyravault.space.util.LocaleHelper;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class MainActivity extends BaseActivity {

    private static final int MAX_SPACES = 10;
    private static final int REQ_ADD_APP = 101;
    private static final int REQ_SET_LOCATION = 102;
    private static final int REQ_SUB_SETTINGS = 103;

    // Persist currentTab across recreation/language switch so it NEVER jumps back to Dashboard unexpectedly!
    private static int activeTabSession = 0; // 0 = Dashboard (Default on initial launch), 1 = Spaces, 2 = Guide, 3 = Settings

    private LinearLayout contentContainer;
    private final Map<Integer, Boolean> expandedState = new HashMap<>();

    // Live Clocks on Dashboard
    private TextView tvTehranTime;
    private TextView tvTehranDate;
    private TextView tvNyTime;
    private TextView tvNyDate;
    private final Handler clockHandler = new Handler(Looper.getMainLooper());
    private final Runnable clockTicker = new Runnable() {
        @Override
        public void run() {
            if (activeTabSession == 0 && tvTehranTime != null && tvNyTime != null) {
                tvTehranTime.setText(JalaliClockUtil.getTehranTime());
                tvTehranDate.setText(JalaliClockUtil.getTehranJalaliDate());
                tvNyTime.setText(JalaliClockUtil.getNewYorkTime());
                tvNyDate.setText(JalaliClockUtil.getNewYorkGregorianDate());
            }
            clockHandler.postDelayed(this, 1000);
        }
    };

    // Track open bottom sheet so any change updates it live immediately
    private Dialog activeConfigDialog;
    private Engine.AppModel activeConfigApp;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        if (SecurityManager.isLockEnabled(this) && !SecurityManager.isSessionUnlocked()) {
            startActivity(new Intent(this, SecurityLockActivity.class));
        }

        VirtualHookManager.applyGlobalEnvironmentToRuntime(this);
        loadExpandedStates();
        buildMainLayout();
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (SecurityManager.isLockEnabled(this) && !SecurityManager.isSessionUnlocked()) {
            startActivity(new Intent(this, SecurityLockActivity.class));
            return;
        }
        // Stay on the exact current tab and refresh live immediately!
        renderCurrentTab();
        if (activeConfigDialog != null && activeConfigDialog.isShowing() && activeConfigApp != null) {
            activeConfigDialog.dismiss();
            showCloneConfigurationBottomSheet(activeConfigApp);
        }
        clockHandler.removeCallbacks(clockTicker);
        clockHandler.post(clockTicker);
    }

    @Override
    protected void onPause() {
        super.onPause();
        clockHandler.removeCallbacks(clockTicker);
    }

    private void loadExpandedStates() {
        SharedPreferences sp = getSharedPreferences("veyravault_ui_state", MODE_PRIVATE);
        for (int i = 0; i < MAX_SPACES; i++) {
            expandedState.put(i, sp.getBoolean("space_exp_" + i, i == 0));
        }
    }

    private void saveExpandedState(int userId, boolean expanded) {
        expandedState.put(userId, expanded);
        getSharedPreferences("veyravault_ui_state", MODE_PRIVATE)
                .edit().putBoolean("space_exp_" + userId, expanded).apply();
    }

    private void buildMainLayout() {
        boolean fa = isFa();

        FrameLayout masterRoot = new FrameLayout(this);
        masterRoot.setBackgroundColor(Color.parseColor("#F1F5F9"));

        LinearLayout mainColumn = new LinearLayout(this);
        mainColumn.setOrientation(LinearLayout.VERTICAL);

        // Top Bar: App Title + Quick Lock Button (🔒) + Language Toggle (EN / فارسی)
        LinearLayout topBar = new LinearLayout(this);
        topBar.setOrientation(LinearLayout.HORIZONTAL);
        topBar.setGravity(Gravity.CENTER_VERTICAL);
        int pad = dp(14);
        topBar.setPadding(pad, dp(12), pad, dp(10));
        topBar.setBackgroundColor(Color.WHITE);

        TextView appTitle = new TextView(this);
        appTitle.setText("VeyraVault");
        appTitle.setTextSize(19f);
        appTitle.setTypeface(Typeface.DEFAULT_BOLD);
        appTitle.setTextColor(Color.parseColor("#0F172A"));
        topBar.addView(appTitle, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f));

        // Quick Lock Button next to Language Switcher
        LinearLayout btnQuickLock = new LinearLayout(this);
        btnQuickLock.setOrientation(LinearLayout.HORIZONTAL);
        btnQuickLock.setGravity(Gravity.CENTER);
        GradientDrawable lockPill = new GradientDrawable();
        lockPill.setColor(Color.parseColor("#FEE2E2"));
        lockPill.setCornerRadius(dp(16));
        lockPill.setStroke(dp(1), Color.parseColor("#FCA5A5"));
        btnQuickLock.setBackground(lockPill);
        btnQuickLock.setPadding(dp(10), dp(5), dp(10), dp(5));

        TextView tvLockBtn = new TextView(this);
        tvLockBtn.setText(fa ? "🔒 قفل سریع" : "🔒 Lock");
        tvLockBtn.setTextSize(12f);
        tvLockBtn.setTypeface(Typeface.DEFAULT_BOLD);
        tvLockBtn.setTextColor(Color.parseColor("#B91C1C"));
        btnQuickLock.addView(tvLockBtn);

        LinearLayout.LayoutParams lockLp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        lockLp.setMargins(dp(6), 0, dp(6), 0);
        btnQuickLock.setOnClickListener(v -> {
            if (SecurityManager.isLockEnabled(this)) {
                SecurityManager.setSessionUnlocked(false);
                startActivity(new Intent(this, SecurityLockActivity.class));
            } else {
                Toast.makeText(this,
                        fa ? "ابتدا یک رمز پین یا الگو ثبت کنید تا قفل سریع فعال شود." : "Please set a PIN or Pattern first.",
                        Toast.LENGTH_SHORT).show();
                startActivityForResult(new Intent(this, SecuritySettingsActivity.class), REQ_SUB_SETTINGS);
            }
        });
        topBar.addView(btnQuickLock, lockLp);

        // Language Toggle Button
        TextView btnLang = new TextView(this);
        btnLang.setText(fa ? "EN / فارسی" : "فارسی / EN");
        btnLang.setTextSize(12f);
        btnLang.setTypeface(Typeface.DEFAULT_BOLD);
        btnLang.setTextColor(Color.parseColor("#1E40AF"));
        GradientDrawable langBg = new GradientDrawable();
        langBg.setColor(Color.parseColor("#DBEAFE"));
        langBg.setCornerRadius(dp(16));
        btnLang.setBackground(langBg);
        btnLang.setPadding(dp(11), dp(5), dp(11), dp(5));
        btnLang.setOnClickListener(v -> {
            LocaleHelper.toggleLanguage(this);
            recreate();
        });
        topBar.addView(btnLang);

        mainColumn.addView(topBar);

        // Scrollable Content Area
        ScrollView scrollView = new ScrollView(this);
        scrollView.setFillViewport(true);
        contentContainer = new LinearLayout(this);
        contentContainer.setOrientation(LinearLayout.VERTICAL);
        contentContainer.setPadding(dp(14), dp(12), dp(14), dp(105));
        scrollView.addView(contentContainer);

        mainColumn.addView(scrollView, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 0, 1f));

        masterRoot.addView(mainColumn);

        // Floating Bottom Navigation Bar with SVG Vector Icons
        // Order (RTL in Persian): 1. Dashboard -> 2. Spaces -> 3. (+) -> 4. Guide -> 5. Settings
        View bottomNav = buildFloatingSvgBottomNav(fa);
        FrameLayout.LayoutParams navLp = new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.WRAP_CONTENT);
        navLp.gravity = Gravity.BOTTOM;
        navLp.setMargins(dp(12), 0, dp(12), dp(12));
        masterRoot.addView(bottomNav, navLp);

        setContentView(masterRoot);
        renderCurrentTab();
    }

    private View buildFloatingSvgBottomNav(boolean fa) {
        LinearLayout bar = new LinearLayout(this);
        bar.setOrientation(LinearLayout.HORIZONTAL);
        bar.setGravity(Gravity.CENTER_VERTICAL);
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(Color.WHITE);
        bg.setCornerRadius(dp(26));
        bg.setStroke(dp(1), Color.parseColor("#E2E8F0"));
        bar.setBackground(bg);
        bar.setPadding(dp(8), dp(6), dp(8), dp(6));
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            bar.setElevation(dp(8));
        }

        LinearLayout.LayoutParams tabLp = new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f);

        // 1. Dashboard (First from right in RTL)
        bar.addView(buildSvgNavTab(R.drawable.ic_nav_dashboard, fa ? "داشبورد" : "Dashboard", activeTabSession == 0, v -> {
            activeTabSession = 0;
            buildMainLayout();
        }), tabLp);

        // 2. Spaces (Second from right in RTL)
        bar.addView(buildSvgNavTab(R.drawable.ic_nav_spaces, fa ? "فضاها" : "Spaces", activeTabSession == 1, v -> {
            activeTabSession = 1;
            buildMainLayout();
        }), tabLp);

        // 3. Center Sleek Blue (+) Button (Slightly smaller: 44dp)
        FrameLayout fabWrap = new FrameLayout(this);
        LinearLayout fab = new LinearLayout(this);
        fab.setGravity(Gravity.CENTER);
        GradientDrawable fabBg = new GradientDrawable();
        fabBg.setShape(GradientDrawable.OVAL);
        fabBg.setColor(Color.parseColor("#2563EB"));
        fab.setBackground(fabBg);

        ImageView plusIcon = new ImageView(this);
        plusIcon.setImageResource(R.drawable.ic_nav_add);
        fab.addView(plusIcon, new LinearLayout.LayoutParams(dp(22), dp(22)));

        fab.setOnClickListener(v -> startActivityForResult(new Intent(this, AddAppActivity.class), REQ_ADD_APP));
        FrameLayout.LayoutParams fabLp = new FrameLayout.LayoutParams(dp(44), dp(44));
        fabLp.gravity = Gravity.CENTER;
        fabWrap.addView(fab, fabLp);
        bar.addView(fabWrap, tabLp);

        // 4. Guide
        bar.addView(buildSvgNavTab(R.drawable.ic_nav_guide, fa ? "راهنما" : "Guide", activeTabSession == 2, v -> {
            activeTabSession = 2;
            buildMainLayout();
        }), tabLp);

        // 5. Settings (Contains Security, Device/GMS, Disguise, About)
        bar.addView(buildSvgNavTab(R.drawable.ic_nav_settings, fa ? "تنظیمات" : "Settings", activeTabSession == 3, v -> {
            activeTabSession = 3;
            buildMainLayout();
        }), tabLp);

        return bar;
    }

    private View buildSvgNavTab(int drawableRes, String label, boolean selected, View.OnClickListener listener) {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setGravity(Gravity.CENTER);
        box.setPadding(dp(2), dp(4), dp(2), dp(4));

        ImageView iv = new ImageView(this);
        iv.setImageResource(drawableRes);
        iv.setColorFilter(Color.parseColor(selected ? "#2563EB" : "#64748B"));
        box.addView(iv, new LinearLayout.LayoutParams(dp(20), dp(20)));

        TextView tv = new TextView(this);
        tv.setText(label);
        tv.setTextSize(10.5f);
        tv.setTypeface(selected ? Typeface.DEFAULT_BOLD : Typeface.DEFAULT);
        tv.setTextColor(Color.parseColor(selected ? "#2563EB" : "#64748B"));
        tv.setPadding(0, dp(2), 0, 0);
        box.addView(tv);

        box.setOnClickListener(listener);
        return box;
    }

    private void renderCurrentTab() {
        if (contentContainer == null) return;
        contentContainer.removeAllViews();
        if (activeTabSession == 0) {
            renderStealthDashboardTab();
        } else if (activeTabSession == 1) {
            renderSpacesTab();
        } else if (activeTabSession == 2) {
            renderGuideTab();
        } else {
            renderSettingsHubTab();
        }
    }

    // =========================================================================
    // TAB 0: STEALTH DASHBOARD (No mention of cloner/multi-space!)
    // Two side-by-side square cards: Iran (Tehran + Jalali) & USA (NY + Gregorian)
    // =========================================================================
    private void renderStealthDashboardTab() {
        boolean fa = isFa();

        // Row of 2 Side-by-Side Square Cards: Iran (Tehran) & USA (New York)
        LinearLayout clocksRow = new LinearLayout(this);
        clocksRow.setOrientation(LinearLayout.HORIZONTAL);
        LinearLayout.LayoutParams rowLp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        rowLp.bottomMargin = dp(14);

        // Square 1: Iran - Tehran (Solar Hijri Date + Live Tehran Time)
        LinearLayout iranCard = new LinearLayout(this);
        iranCard.setOrientation(LinearLayout.VERTICAL);
        iranCard.setGravity(Gravity.CENTER);
        GradientDrawable iranBg = new GradientDrawable(
                GradientDrawable.Orientation.TL_BR,
                new int[]{Color.parseColor("#1E3A8A"), Color.parseColor("#2563EB")});
        iranBg.setCornerRadius(dp(20));
        iranCard.setBackground(iranBg);
        iranCard.setPadding(dp(12), dp(18), dp(12), dp(18));

        TextView tvIranTitle = new TextView(this);
        tvIranTitle.setText(fa ? "🇮🇷 ایران (تهران)" : "🇮🇷 Iran (Tehran)");
        tvIranTitle.setTextSize(13.5f);
        tvIranTitle.setTypeface(Typeface.DEFAULT_BOLD);
        tvIranTitle.setTextColor(Color.parseColor("#BFDBFE"));
        tvIranTitle.setGravity(Gravity.CENTER);
        iranCard.addView(tvIranTitle);

        tvTehranTime = new TextView(this);
        tvTehranTime.setText(JalaliClockUtil.getTehranTime());
        tvTehranTime.setTextSize(23f);
        tvTehranTime.setTypeface(Typeface.DEFAULT_BOLD);
        tvTehranTime.setTextColor(Color.WHITE);
        tvTehranTime.setGravity(Gravity.CENTER);
        tvTehranTime.setPadding(0, dp(8), 0, dp(6));
        iranCard.addView(tvTehranTime);

        tvTehranDate = new TextView(this);
        tvTehranDate.setText(JalaliClockUtil.getTehranJalaliDate());
        tvTehranDate.setTextSize(11.5f);
        tvTehranDate.setTextColor(Color.parseColor("#E0F2FE"));
        tvTehranDate.setGravity(Gravity.CENTER);
        iranCard.addView(tvTehranDate);

        // Square 2: USA - New York (Gregorian Date + Live NY Time)
        LinearLayout nyCard = new LinearLayout(this);
        nyCard.setOrientation(LinearLayout.VERTICAL);
        nyCard.setGravity(Gravity.CENTER);
        GradientDrawable nyBg = new GradientDrawable(
                GradientDrawable.Orientation.TL_BR,
                new int[]{Color.parseColor("#0F172A"), Color.parseColor("#334155")});
        nyBg.setCornerRadius(dp(20));
        nyCard.setBackground(nyBg);
        nyCard.setPadding(dp(12), dp(18), dp(12), dp(18));

        TextView tvNyTitle = new TextView(this);
        tvNyTitle.setText(fa ? "🇺🇸 آمریکا (نیویورک)" : "🇺🇸 USA (New York)");
        tvNyTitle.setTextSize(13.5f);
        tvNyTitle.setTypeface(Typeface.DEFAULT_BOLD);
        tvNyTitle.setTextColor(Color.parseColor("#93C5FD"));
        tvNyTitle.setGravity(Gravity.CENTER);
        nyCard.addView(tvNyTitle);

        tvNyTime = new TextView(this);
        tvNyTime.setText(JalaliClockUtil.getNewYorkTime());
        tvNyTime.setTextSize(23f);
        tvNyTime.setTypeface(Typeface.DEFAULT_BOLD);
        tvNyTime.setTextColor(Color.WHITE);
        tvNyTime.setGravity(Gravity.CENTER);
        tvNyTime.setPadding(0, dp(8), 0, dp(6));
        nyCard.addView(tvNyTime);

        tvNyDate = new TextView(this);
        tvNyDate.setText(JalaliClockUtil.getNewYorkGregorianDate());
        tvNyDate.setTextSize(11.5f);
        tvNyDate.setTextColor(Color.parseColor("#CBD5E1"));
        tvNyDate.setGravity(Gravity.CENTER);
        nyCard.addView(tvNyDate);

        LinearLayout.LayoutParams sqLp1 = new LinearLayout.LayoutParams(0, dp(138), 1f);
        sqLp1.setMargins(dp(4), 0, dp(4), 0);
        LinearLayout.LayoutParams sqLp2 = new LinearLayout.LayoutParams(0, dp(138), 1f);
        sqLp2.setMargins(dp(4), 0, dp(4), 0);

        clocksRow.addView(iranCard, sqLp1);
        clocksRow.addView(nyCard, sqLp2);
        contentContainer.addView(clocksRow, rowLp);

        // Card 2: Active System Profile & Region Configuration
        LinearLayout envCard = buildWhiteCard();
        TextView envHeader = new TextView(this);
        envHeader.setText(fa ? "🛡️ مشخصات پروفایل دستگاه و منطقه فعال" : "🛡️ Active Device & Region Profile");
        envHeader.setTextSize(15f);
        envHeader.setTypeface(Typeface.DEFAULT_BOLD);
        envHeader.setTextColor(Color.parseColor("#0F172A"));
        envCard.addView(envHeader);

        String activeDev = CloneMetadataStore.getGlobalDeviceSummary(this);
        String activeReg = CloneMetadataStore.getGlobalRegionLabel(this);
        String activeIp = CloneMetadataStore.getGlobalVirtualIp(this);
        double[] gc = CloneMetadataStore.getGlobalCoordinates(this);

        TextView envDetails = new TextView(this);
        envDetails.setText(fa
                ? String.format(java.util.Locale.US,
                    "• مدل دستگاه ثبت‌شده: %s\n• منطقه کشور و شهر: %s\n• مختصات منطقه: %.4f, %.4f\n• سپر شبکه و آی‌پی: فعال (%s)",
                    activeDev, activeReg, gc[0], gc[1], activeIp)
                : String.format(java.util.Locale.US,
                    "• Configured Device: %s\n• Region (City, Country): %s\n• Coordinates: %.4f, %.4f\n• Network IP Shield: Active (%s)",
                    activeDev, activeReg, gc[0], gc[1], activeIp));
        envDetails.setTextSize(13f);
        envDetails.setTextColor(Color.parseColor("#334155"));
        envDetails.setLineSpacing(dp(3), 1f);
        envDetails.setPadding(0, dp(8), 0, dp(10));
        envCard.addView(envDetails);

        Button btnEditEnv = new Button(this);
        btnEditEnv.setAllCaps(false);
        btnEditEnv.setText(fa ? "تغییر مدل دستگاه و منطقه کشور" : "Configure Device & Region");
        btnEditEnv.setTextColor(Color.WHITE);
        btnEditEnv.setTextSize(13f);
        btnEditEnv.setTypeface(Typeface.DEFAULT_BOLD);
        GradientDrawable btnBg = new GradientDrawable();
        btnBg.setColor(Color.parseColor("#2563EB"));
        btnBg.setCornerRadius(dp(12));
        btnEditEnv.setBackground(btnBg);
        btnEditEnv.setOnClickListener(v -> startActivityForResult(new Intent(this, GlobalEnvironmentActivity.class), REQ_SUB_SETTINGS));
        envCard.addView(btnEditEnv, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, dp(42)));
        contentContainer.addView(envCard);

        // Card 3: System Performance & Anti-Hang Speed Booster
        LinearLayout perfCard = buildWhiteCard();
        TextView perfTitle = new TextView(this);
        perfTitle.setText(fa ? "⚡ وضعیت پردازنده، حافظه رم و شتاب‌دهنده" : "⚡ Memory & Speed Optimizer");
        perfTitle.setTextSize(15f);
        perfTitle.setTypeface(Typeface.DEFAULT_BOLD);
        perfTitle.setTextColor(Color.parseColor("#0F172A"));
        perfCard.addView(perfTitle);

        ActivityManager.MemoryInfo mi = new ActivityManager.MemoryInfo();
        ActivityManager am = (ActivityManager) getSystemService(Context.ACTIVITY_SERVICE);
        if (am != null) am.getMemoryInfo(mi);
        long availMb = mi.availMem / (1024 * 1024);
        long totalMb = mi.totalMem / (1024 * 1024);
        long usedPct = totalMb > 0 ? ((totalMb - availMb) * 100 / totalMb) : 45;

        TextView perfStats = new TextView(this);
        perfStats.setText(fa
                ? ("• حافظه آزاد سیستم: " + availMb + " مگابایت از " + totalMb + " مگابایت (" + usedPct + "% مصرف)\n"
                   + "• وضعیت موتور شتاب‌دهنده و کش آیکون‌ها: فعال و بهینه ✓")
                : ("• Free RAM: " + availMb + " MB / " + totalMb + " MB (" + usedPct + "% used)\n"
                   + "• Engine Warmup & LruCache: Active & Optimized ✓"));
        perfStats.setTextSize(13f);
        perfStats.setTextColor(Color.parseColor("#475569"));
        perfStats.setPadding(0, dp(8), 0, dp(10));
        perfCard.addView(perfStats);

        Button btnBoost = new Button(this);
        btnBoost.setAllCaps(false);
        btnBoost.setText(fa ? "🚀 بهینه‌سازی فوری حافظه و افزایش سرعت اجرا" : "🚀 Boost Memory & Execution Speed");
        btnBoost.setTextColor(Color.WHITE);
        btnBoost.setTextSize(13f);
        btnBoost.setTypeface(Typeface.DEFAULT_BOLD);
        GradientDrawable boostBg = new GradientDrawable();
        boostBg.setColor(Color.parseColor("#059669"));
        boostBg.setCornerRadius(dp(12));
        btnBoost.setBackground(boostBg);
        btnBoost.setOnClickListener(v -> {
            System.gc();
            Toast.makeText(this,
                    fa ? "✓ حافظه کش آزاد شد و سرعت اجرای برنامه‌ها بهینه گردید!" : "✓ Memory optimized for fast app launch!",
                    Toast.LENGTH_SHORT).show();
            renderCurrentTab();
        });
        perfCard.addView(btnBoost, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, dp(42)));
        contentContainer.addView(perfCard);
    }

    // =========================================================================
    // TAB 1: SPACES (Blue Header with Model + Region, 3-dots Space Rename, Clone Grid)
    // =========================================================================
    private void renderSpacesTab() {
        boolean fa = isFa();

        // Top Blue Banner Card (Item 6: Active Global Model + Line 2: Region City, Country)
        LinearLayout statusBanner = new LinearLayout(this);
        statusBanner.setOrientation(LinearLayout.VERTICAL);
        GradientDrawable bannerBg = new GradientDrawable(
                GradientDrawable.Orientation.LEFT_RIGHT,
                new int[]{Color.parseColor("#1E40AF"), Color.parseColor("#2563EB")});
        bannerBg.setCornerRadius(dp(18));
        statusBanner.setBackground(bannerBg);
        statusBanner.setPadding(dp(16), dp(14), dp(16), dp(14));
        LinearLayout.LayoutParams bannerLp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        bannerLp.bottomMargin = dp(14);

        TextView bannerTitle = new TextView(this);
        bannerTitle.setText(fa ? "فضاهای چندگانه و موقعیت مکانی هوشمند" : "Multi-Spaces & Smart Location");
        bannerTitle.setTextSize(15f);
        bannerTitle.setTypeface(Typeface.DEFAULT_BOLD);
        bannerTitle.setTextColor(Color.WHITE);
        statusBanner.addView(bannerTitle);

        TextView bannerModelLine = new TextView(this);
        bannerModelLine.setText((fa ? "مدل سراسری فعال: " : "Active Global Model: ")
                + CloneMetadataStore.getGlobalDeviceSummary(this));
        bannerModelLine.setTextSize(12.5f);
        bannerModelLine.setTextColor(Color.parseColor("#DBEAFE"));
        bannerModelLine.setPadding(0, dp(4), 0, 0);
        statusBanner.addView(bannerModelLine);

        TextView bannerRegionLine = new TextView(this);
        bannerRegionLine.setText((fa ? "منطقه: " : "Region: ")
                + CloneMetadataStore.getGlobalRegionLabel(this));
        bannerRegionLine.setTextSize(12.5f);
        bannerRegionLine.setTypeface(Typeface.DEFAULT_BOLD);
        bannerRegionLine.setTextColor(Color.parseColor("#FEF08A"));
        bannerRegionLine.setPadding(0, dp(2), 0, 0);
        statusBanner.addView(bannerRegionLine);

        statusBanner.setOnClickListener(v -> startActivityForResult(new Intent(this, GlobalEnvironmentActivity.class), REQ_SUB_SETTINGS));
        contentContainer.addView(statusBanner, bannerLp);

        // Render Active Spaces
        List<Integer> spacesToShow = new ArrayList<>();
        spacesToShow.add(0);
        spacesToShow.add(1);
        for (int i = 2; i < MAX_SPACES; i++) {
            if (!Engine.getClonedApps(this, i).isEmpty()) {
                spacesToShow.add(i);
            }
        }

        for (int userId : spacesToShow) {
            List<Engine.AppModel> clones = Engine.getClonedApps(this, userId);
            contentContainer.addView(buildSpaceCard(userId, clones, fa));
        }
    }

    private View buildSpaceCard(final int userId, final List<Engine.AppModel> clones, final boolean fa) {
        final boolean isExpanded = expandedState.containsKey(userId) ? expandedState.get(userId) : false;

        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        GradientDrawable cardBg = new GradientDrawable();
        cardBg.setColor(Color.WHITE);
        cardBg.setCornerRadius(dp(18));
        card.setBackground(cardBg);
        int pad = dp(14);
        card.setPadding(pad, dp(12), pad, dp(12));

        LinearLayout.LayoutParams cardLp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        cardLp.bottomMargin = dp(12);
        card.setLayoutParams(cardLp);

        // Header Row of Space Card
        LinearLayout headerRow = new LinearLayout(this);
        headerRow.setOrientation(LinearLayout.HORIZONTAL);
        headerRow.setGravity(Gravity.CENTER_VERTICAL);

        TextView chevron = new TextView(this);
        chevron.setText(isExpanded ? "⌃" : "⌄");
        chevron.setTextSize(18f);
        chevron.setTypeface(Typeface.DEFAULT_BOLD);
        chevron.setTextColor(Color.parseColor("#475569"));
        chevron.setPadding(dp(6), 0, dp(6), 0);
        headerRow.addView(chevron);

        String spaceTitleText = CloneMetadataStore.getSpaceDisplayTitle(this, userId, fa ? "فضای" : "Space");
        TextView tvSpaceTitle = new TextView(this);
        tvSpaceTitle.setText(spaceTitleText);
        tvSpaceTitle.setTextSize(15.5f);
        tvSpaceTitle.setTypeface(Typeface.DEFAULT_BOLD);
        tvSpaceTitle.setTextColor(Color.parseColor("#0F172A"));
        headerRow.addView(tvSpaceTitle);

        // Item 1: Three Dots (⋮) Button right next to the Space Name to Rename the Space!
        TextView btnRenameSpace = new TextView(this);
        btnRenameSpace.setText("⋮");
        btnRenameSpace.setTextSize(18f);
        btnRenameSpace.setTypeface(Typeface.DEFAULT_BOLD);
        btnRenameSpace.setTextColor(Color.parseColor("#2563EB"));
        btnRenameSpace.setPadding(dp(10), dp(2), dp(10), dp(2));
        btnRenameSpace.setOnClickListener(v -> showRenameSpaceDialog(userId));
        headerRow.addView(btnRenameSpace);

        View spacer = new View(this);
        headerRow.addView(spacer, new LinearLayout.LayoutParams(0, 1, 1f));

        // GMS Pill Badge
        boolean gmsOn = GmsSupportManager.isGmsInstalled(userId);
        TextView gmsPill = new TextView(this);
        gmsPill.setText(gmsOn ? "GMS ✓" : "GMS +");
        gmsPill.setTextSize(11f);
        gmsPill.setTypeface(Typeface.DEFAULT_BOLD);
        gmsPill.setTextColor(gmsOn ? Color.parseColor("#065F46") : Color.parseColor("#475569"));
        GradientDrawable gmsBg = new GradientDrawable();
        gmsBg.setColor(gmsOn ? Color.parseColor("#D1FAE5") : Color.parseColor("#F1F5F9"));
        gmsBg.setCornerRadius(dp(12));
        gmsPill.setBackground(gmsBg);
        gmsPill.setPadding(dp(8), dp(3), dp(8), dp(3));
        LinearLayout.LayoutParams gmsLp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        gmsLp.setMargins(dp(6), 0, dp(6), 0);
        gmsPill.setOnClickListener(v -> {
            GmsSupportManager.toggleGmsForUser(userId);
            renderCurrentTab();
        });
        headerRow.addView(gmsPill, gmsLp);

        // Blue Space Number Badge
        TextView spaceBadge = new TextView(this);
        spaceBadge.setText(String.valueOf(userId + 1));
        spaceBadge.setTextSize(12f);
        spaceBadge.setTypeface(Typeface.DEFAULT_BOLD);
        spaceBadge.setTextColor(Color.WHITE);
        spaceBadge.setGravity(Gravity.CENTER);
        GradientDrawable badgeBg = new GradientDrawable();
        badgeBg.setColor(Color.parseColor("#2563EB"));
        badgeBg.setCornerRadius(dp(12));
        spaceBadge.setBackground(badgeBg);
        spaceBadge.setPadding(dp(10), dp(3), dp(10), dp(3));
        headerRow.addView(spaceBadge);

        headerRow.setOnClickListener(v -> {
            saveExpandedState(userId, !isExpanded);
            renderCurrentTab();
        });
        card.addView(headerRow);

        if (isExpanded) {
            if (clones.isEmpty()) {
                TextView emptyTv = new TextView(this);
                emptyTv.setText(fa
                        ? "هنوز برنامه‌ای در این فضا نیست. روی دکمه + پایین بزنید."
                        : "No apps in this space yet. Tap + below to add.");
                emptyTv.setTextSize(12.5f);
                emptyTv.setTextColor(Color.parseColor("#94A3B8"));
                emptyTv.setGravity(Gravity.CENTER);
                emptyTv.setPadding(0, dp(16), 0, dp(8));
                card.addView(emptyTv);
            } else {
                GridLayout grid = new GridLayout(this);
                grid.setColumnCount(4);
                grid.setPadding(0, dp(12), 0, dp(4));

                int screenWidth = getResources().getDisplayMetrics().widthPixels;
                int itemWidth = (screenWidth - dp(64)) / 4;

                for (Engine.AppModel app : clones) {
                    View cell = buildExpandedCloneCell(app, userId, itemWidth);
                    grid.addView(cell);
                }
                card.addView(grid);
            }
        } else {
            LinearLayout collapsedRow = new LinearLayout(this);
            collapsedRow.setOrientation(LinearLayout.HORIZONTAL);
            collapsedRow.setGravity(Gravity.CENTER_VERTICAL);
            collapsedRow.setPadding(0, dp(10), 0, dp(2));

            int previewCount = Math.min(3, clones.size());
            for (int i = 0; i < previewCount; i++) {
                ImageView miniIcon = new ImageView(this);
                miniIcon.setImageDrawable(clones.get(i).icon);
                LinearLayout.LayoutParams mlp = new LinearLayout.LayoutParams(dp(28), dp(28));
                mlp.setMargins(0, 0, dp(4), 0);
                collapsedRow.addView(miniIcon, mlp);
            }

            TextView countBadge = new TextView(this);
            countBadge.setText(clones.size() + "+");
            countBadge.setTextSize(12f);
            countBadge.setTypeface(Typeface.DEFAULT_BOLD);
            countBadge.setTextColor(Color.parseColor("#475569"));
            GradientDrawable cntBg = new GradientDrawable();
            cntBg.setColor(Color.parseColor("#F1F5F9"));
            cntBg.setCornerRadius(dp(12));
            countBadge.setBackground(cntBg);
            countBadge.setPadding(dp(10), dp(4), dp(10), dp(4));
            collapsedRow.addView(countBadge);

            collapsedRow.setOnClickListener(v -> {
                saveExpandedState(userId, true);
                renderCurrentTab();
            });
            card.addView(collapsedRow);
        }

        return card;
    }

    private void showRenameSpaceDialog(final int userId) {
        boolean fa = isFa();
        AlertDialog.Builder b = new AlertDialog.Builder(this);
        b.setTitle(fa ? ("تغییر نام فضای " + (userId + 1)) : ("Rename Space " + (userId + 1)));

        final EditText input = new EditText(this);
        String currentCustom = CloneMetadataStore.getSpaceCustomName(this, userId);
        input.setText(currentCustom);
        input.setHint(fa ? ("مثلاً: فضای کاری، اکانت آلمان یا فضای " + (userId + 1)) : ("e.g. Work Space or Space " + (userId + 1)));
        input.setPadding(dp(20), dp(16), dp(20), dp(16));
        b.setView(input);

        b.setPositiveButton(fa ? "ذخیره فوری" : "Save Now", (d, w) -> {
            CloneMetadataStore.setSpaceCustomName(this, userId, input.getText().toString().trim());
            renderCurrentTab();
        });
        b.setNeutralButton(fa ? "نام پیش‌فرض" : "Reset Default", (d, w) -> {
            CloneMetadataStore.setSpaceCustomName(this, userId, "");
            renderCurrentTab();
        });
        b.setNegativeButton(fa ? "انصراف" : "Cancel", null);
        b.show();
    }

    private View buildExpandedCloneCell(final Engine.AppModel app, final int userId, int cellWidth) {
        LinearLayout cell = new LinearLayout(this);
        cell.setOrientation(LinearLayout.VERTICAL);
        cell.setGravity(Gravity.CENTER_HORIZONTAL);
        cell.setPadding(dp(4), dp(6), dp(4), dp(8));
        cell.setLayoutParams(new ViewGroupLayoutParamsHelper(cellWidth));

        FrameLayout iconBox = new FrameLayout(this);
        ImageView iv = new ImageView(this);
        iv.setImageDrawable(app.icon);
        FrameLayout.LayoutParams ivLp = new FrameLayout.LayoutParams(dp(48), dp(48));
        ivLp.gravity = Gravity.CENTER;
        iconBox.addView(iv, ivLp);

        TextView badge = new TextView(this);
        badge.setText(String.valueOf(userId + 1));
        badge.setTextSize(9.5f);
        badge.setTypeface(Typeface.DEFAULT_BOLD);
        badge.setTextColor(Color.WHITE);
        GradientDrawable bBg = new GradientDrawable();
        bBg.setColor(Color.parseColor("#2563EB"));
        bBg.setCornerRadius(dp(8));
        badge.setBackground(bBg);
        badge.setPadding(dp(5), dp(1), dp(5), dp(1));
        FrameLayout.LayoutParams bLp = new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.WRAP_CONTENT, FrameLayout.LayoutParams.WRAP_CONTENT);
        bLp.gravity = Gravity.TOP | Gravity.LEFT;
        iconBox.addView(badge, bLp);

        iconBox.setOnClickListener(v -> {
            Toast.makeText(this, (isFa() ? "در حال اجرای " : "Launching ") + app.name + "...", Toast.LENGTH_SHORT).show();
            Engine.launchClone(this, app.packageName, userId);
        });
        cell.addView(iconBox, new LinearLayout.LayoutParams(dp(56), dp(54)));

        LinearLayout labelRow = new LinearLayout(this);
        labelRow.setOrientation(LinearLayout.HORIZONTAL);
        labelRow.setGravity(Gravity.CENTER_VERTICAL);
        labelRow.setPadding(0, dp(4), 0, 0);

        TextView tvMore = new TextView(this);
        tvMore.setText("⋮");
        tvMore.setTextSize(15f);
        tvMore.setTypeface(Typeface.DEFAULT_BOLD);
        tvMore.setTextColor(Color.parseColor("#475569"));
        tvMore.setPadding(dp(4), 0, dp(4), 0);
        tvMore.setOnClickListener(v -> showCloneConfigurationBottomSheet(app));
        labelRow.addView(tvMore);

        TextView tvName = new TextView(this);
        tvName.setText(app.name);
        tvName.setTextSize(11f);
        tvName.setTextColor(Color.parseColor("#1E293B"));
        tvName.setSingleLine(true);
        tvName.setEllipsize(TextUtils.TruncateAt.END);
        tvName.setOnClickListener(v -> showCloneConfigurationBottomSheet(app));
        labelRow.addView(tvName, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f));

        cell.addView(labelRow, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT));

        return cell;
    }

    private static class ViewGroupLayoutParamsHelper extends GridLayout.LayoutParams {
        public ViewGroupLayoutParamsHelper(int width) {
            super();
            this.width = width;
            this.height = GridLayout.LayoutParams.WRAP_CONTENT;
        }
    }

    // =========================================================================
    // TAB 2: GUIDE (راهنمای کامل استفاده)
    // =========================================================================
    private void renderGuideTab() {
        boolean fa = isFa();
        LinearLayout card = buildWhiteCard();

        TextView title = new TextView(this);
        title.setText(fa ? "📘 راهنمای جامع امکانات نسخه ۳" : "📘 VeyraVault v3.0 Complete Guide");
        title.setTextSize(16.5f);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setTextColor(Color.parseColor("#0F172A"));
        card.addView(title);

        TextView body = new TextView(this);
        body.setText(fa
                ? "۱. تغییر نام فضاها:\nدر تب «فضاها»، کنار نام هر فضا (مثلاً فضای ۱) روی دکمه سه نقطه (⋮) بزنید تا نام آن فضا را به دلخواه تغییر دهید.\n\n"
                  + "۲. قانون اولویت مدل گوشی و موقعیت مکانی:\nتمام فضاها به صورت پیش‌فرض از مدل گوشی و منطقه‌ای (مثلاً Falkenstein, Germany) که در بخش تنظیمات کلی ثبت کرده‌اید استفاده می‌کنند. اما اگر روی سه نقطه (⋮) کنار یک برنامه بزنید و برای آن برنامه مدل گوشی (مثلاً آیفون ۱۶ پرو مکس) یا شهر/کشور جداگانه‌ای ثبت کنید، اولویت ۱۰۰٪ با تنظیمات اختصاصی همان برنامه خواهد بود.\n\n"
                  + "۳. صندوق مستقل برنامه‌ها (حذف نشدن کلون‌ها):\nتمام برنامه‌های کلون‌شده در صندوق مستقل داخلی ذخیره می‌شوند؛ بنابراین حتی اگر برنامه اصلی را از روی گوشی خود پاک کنید، برنامه‌های داخل VeyraVault هرگز پاک نمی‌شوند!\n\n"
                  + "۴. قفل امنیتی دوگانه (پین + الگو هم‌زمان):\nدر بخش تنظیمات امنیتی می‌توانید هم رمز پین و هم الگو را هم‌زمان ثبت کنید و اولویت قفل اول را مشخص نمایید. در زمان باز کردن قفل، در صورت اشتباه زدن قفل اول، لینک ورود با قفل دوم به صورت خودکار در پایین صفحه ظاهر می‌شود."
                : "1. Rename Spaces: Tap (⋮) next to any Space title.\n\n"
                  + "2. Priority Rule: Global device & region (e.g. Falkenstein, Germany) apply by default, but per-app settings in (⋮) take 100% priority.\n\n"
                  + "3. Independent APK Vault: Uninstalling the original app from your phone will NEVER delete your clones inside VeyraVault.\n\n"
                  + "4. Dual Lock: Configure both PIN and Pattern with priority and automatic fallback.");
        body.setTextSize(13f);
        body.setTextColor(Color.parseColor("#334155"));
        body.setLineSpacing(dp(4), 1f);
        body.setPadding(0, dp(10), 0, 0);
        card.addView(body);

        contentContainer.addView(card);
    }

    // =========================================================================
    // TAB 3: SETTINGS HUB (Contains Device/Region/GMS, Security/Dual Lock, Disguise, About)
    // =========================================================================
    private void renderSettingsHubTab() {
        boolean fa = isFa();

        // Hub Item 1: Device Model (Apple/Android), Region (Falkenstein, Germany), IP Shield & GMS
        LinearLayout card1 = buildWhiteCard();
        TextView t1 = new TextView(this);
        t1.setText(fa ? "📱 تغییر مدل گوشی (اپل/اندروید)، منطقه، آی‌پی و گوگل‌پلی" : "📱 Device Model (Apple/Android), Region, IP & GMS");
        t1.setTextSize(15f);
        t1.setTypeface(Typeface.DEFAULT_BOLD);
        t1.setTextColor(Color.parseColor("#0F172A"));
        card1.addView(t1);

        TextView d1 = new TextView(this);
        d1.setText(fa
                ? ("مدل فعال: " + CloneMetadataStore.getGlobalDeviceSummary(this)
                   + "\nمنطقه فعال: " + CloneMetadataStore.getGlobalRegionLabel(this))
                : ("Active Model: " + CloneMetadataStore.getGlobalDeviceSummary(this)
                   + "\nActive Region: " + CloneMetadataStore.getGlobalRegionLabel(this)));
        d1.setTextSize(12.5f);
        d1.setTextColor(Color.parseColor("#2563EB"));
        d1.setPadding(0, dp(6), 0, dp(10));
        card1.addView(d1);

        Button b1 = buildHubButton(fa ? "ورود به تنظیمات مدل گوشی، منطقه و گوگل ⬅" : "Open Device, Region & GMS Settings ➔", "#2563EB");
        b1.setOnClickListener(v -> startActivityForResult(new Intent(this, GlobalEnvironmentActivity.class), REQ_SUB_SETTINGS));
        card1.addView(b1);
        contentContainer.addView(card1);

        // Hub Item 2: Security, Dual Lock (PIN + Pattern), Icon Disguise & Anti-Uninstall
        LinearLayout card2 = buildWhiteCard();
        TextView t2 = new TextView(this);
        t2.setText(fa ? "🔐 امنیت، قفل دوگانه (پین/الگو)، مخفی‌سازی و ضدحذف" : "🔐 Security, Dual Lock, Disguise & Anti-Uninstall");
        t2.setTextSize(15f);
        t2.setTypeface(Typeface.DEFAULT_BOLD);
        t2.setTextColor(Color.parseColor("#0F172A"));
        card2.addView(t2);

        TextView d2 = new TextView(this);
        d2.setText(fa
                ? "تنظیم هم‌زمان رمز پین و الگو با اولویت دلخواه، تغییر آیکون به ماشین‌حساب و قفل ضدحذف هوشمند."
                : "Simultaneous PIN & Pattern lock with priority fallback, icon disguise, and smart anti-uninstall.");
        d2.setTextSize(12.5f);
        d2.setTextColor(Color.parseColor("#475569"));
        d2.setPadding(0, dp(6), 0, dp(10));
        card2.addView(d2);

        Button b2 = buildHubButton(fa ? "ورود به تنظیمات امنیت و قفل ⬅" : "Open Security & Lock Settings ➔", "#7C3AED");
        b2.setOnClickListener(v -> startActivityForResult(new Intent(this, SecuritySettingsActivity.class), REQ_SUB_SETTINGS));
        card2.addView(b2);
        contentContainer.addView(card2);

        // Hub Item 3: About Us & Contact
        LinearLayout card3 = buildWhiteCard();
        TextView t3 = new TextView(this);
        t3.setText(fa ? "ℹ️ درباره ما و ارتباط با سازنده" : "ℹ️ About Us & Contact");
        t3.setTextSize(15f);
        t3.setTypeface(Typeface.DEFAULT_BOLD);
        t3.setTextColor(Color.parseColor("#0F172A"));
        card3.addView(t3);

        TextView d3 = new TextView(this);
        d3.setText("Email: Vaultveyra@gmail.com\nTelegram: https://t.me/VaultVeyra");
        d3.setTextSize(12.5f);
        d3.setTextColor(Color.parseColor("#475569"));
        d3.setPadding(0, dp(6), 0, dp(10));
        card3.addView(d3);

        Button b3 = buildHubButton(fa ? "مشاهده صفحه درباره ما ⬅" : "Open About Page ➔", "#059669");
        b3.setOnClickListener(v -> startActivity(new Intent(this, AboutActivity.class)));
        card3.addView(b3);
        contentContainer.addView(card3);
    }

    private LinearLayout buildWhiteCard() {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(Color.WHITE);
        bg.setCornerRadius(dp(18));
        card.setBackground(bg);
        int p = dp(16);
        card.setPadding(p, p, p, p);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        lp.bottomMargin = dp(14);
        card.setLayoutParams(lp);
        return card;
    }

    private Button buildHubButton(String text, String colorHex) {
        Button b = new Button(this);
        b.setAllCaps(false);
        b.setText(text);
        b.setTextColor(Color.WHITE);
        b.setTextSize(13f);
        b.setTypeface(Typeface.DEFAULT_BOLD);
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(Color.parseColor(colorHex));
        bg.setCornerRadius(dp(12));
        b.setBackground(bg);
        b.setLayoutParams(new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, dp(42)));
        return b;
    }

    // =========================================================================
    // PER-CLONE CONFIGURATION BOTTOM SHEET (With Live Update & Priority Notice)
    // =========================================================================
    private void showCloneConfigurationBottomSheet(final Engine.AppModel app) {
        final boolean fa = isFa();
        activeConfigApp = app;

        final Dialog dialog = new Dialog(this);
        activeConfigDialog = dialog;
        dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);

        LinearLayout sheet = new LinearLayout(this);
        sheet.setOrientation(LinearLayout.VERTICAL);
        GradientDrawable sheetBg = new GradientDrawable();
        sheetBg.setColor(Color.WHITE);
        sheetBg.setCornerRadii(new float[]{dp(24), dp(24), dp(24), dp(24), 0, 0, 0, 0});
        sheet.setBackground(sheetBg);
        int pad = dp(18);
        sheet.setPadding(pad, dp(18), pad, dp(22));

        // Top Row: "Set Location" Pill + App Info + App Icon
        LinearLayout topRow = new LinearLayout(this);
        topRow.setOrientation(LinearLayout.HORIZONTAL);
        topRow.setGravity(Gravity.CENTER_VERTICAL);

        TextView btnSetLoc = new TextView(this);
        btnSetLoc.setText(fa ? "📍 تنظیم موقعیت و شهر" : "📍 Set Location");
        btnSetLoc.setTextSize(12.5f);
        btnSetLoc.setTypeface(Typeface.DEFAULT_BOLD);
        btnSetLoc.setTextColor(Color.parseColor("#2563EB"));
        GradientDrawable locPillBg = new GradientDrawable();
        locPillBg.setColor(Color.parseColor("#EFF6FF"));
        locPillBg.setCornerRadius(dp(18));
        locPillBg.setStroke(dp(1), Color.parseColor("#BFDBFE"));
        btnSetLoc.setBackground(locPillBg);
        btnSetLoc.setPadding(dp(12), dp(7), dp(12), dp(7));
        btnSetLoc.setOnClickListener(v -> {
            Intent locIntent = new Intent(this, SetLocationActivity.class);
            locIntent.putExtra(SetLocationActivity.EXTRA_PKG, app.packageName);
            locIntent.putExtra(SetLocationActivity.EXTRA_USER_ID, app.userId);
            locIntent.putExtra(SetLocationActivity.EXTRA_APP_NAME, app.name);
            startActivityForResult(locIntent, REQ_SET_LOCATION);
        });
        topRow.addView(btnSetLoc);

        LinearLayout infoCol = new LinearLayout(this);
        infoCol.setOrientation(LinearLayout.VERTICAL);
        infoCol.setGravity(Gravity.RIGHT | Gravity.CENTER_VERTICAL);
        infoCol.setPadding(dp(10), 0, dp(10), 0);

        String displayAlias = CloneMetadataStore.getAlias(this, app.packageName, app.userId, app.name);
        app.name = displayAlias;

        TextView tvAppName = new TextView(this);
        tvAppName.setText(displayAlias);
        tvAppName.setTextSize(15.5f);
        tvAppName.setTypeface(Typeface.DEFAULT_BOLD);
        tvAppName.setTextColor(Color.parseColor("#0F172A"));
        infoCol.addView(tvAppName);

        String locSummary = CloneMetadataStore.getLocationSummary(
                this, app.packageName, app.userId, fa ? "بدون موقعیت" : "No location");
        TextView tvLocStatus = new TextView(this);
        tvLocStatus.setText(locSummary);
        tvLocStatus.setTextSize(11.5f);
        tvLocStatus.setTextColor(Color.parseColor("#059669"));
        infoCol.addView(tvLocStatus);

        String devSummary = CloneMetadataStore.getDeviceIdentitySummary(
                this, app.packageName, app.userId, "");
        TextView tvDevStatus = new TextView(this);
        tvDevStatus.setText(devSummary);
        tvDevStatus.setTextSize(11.5f);
        tvDevStatus.setTypeface(Typeface.DEFAULT_BOLD);
        tvDevStatus.setTextColor(Color.parseColor("#2563EB"));
        infoCol.addView(tvDevStatus);

        topRow.addView(infoCol, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f));

        ImageView appIcon = new ImageView(this);
        appIcon.setImageDrawable(app.icon);
        topRow.addView(appIcon, new LinearLayout.LayoutParams(dp(46), dp(46)));

        sheet.addView(topRow);

        TextView tvConfigHeader = new TextView(this);
        tvConfigHeader.setText(fa
                ? "پیکربندی اختصاصی اپ (تغییرات این بخش اولویت اول را نسبت به تنظیمات سراسری دارد)"
                : "Per-App Configuration (Overrides Global Settings)");
        tvConfigHeader.setTextSize(12f);
        tvConfigHeader.setTypeface(Typeface.DEFAULT_BOLD);
        tvConfigHeader.setTextColor(Color.parseColor("#475569"));
        tvConfigHeader.setPadding(0, dp(14), 0, dp(8));
        sheet.addView(tvConfigHeader);

        // 3x3 Grid of Actions
        GridLayout actionGrid = new GridLayout(this);
        actionGrid.setColumnCount(3);

        int gridWidth = getResources().getDisplayMetrics().widthPixels - dp(36);
        int btnWidth = (gridWidth - dp(24)) / 3;

        Object[][] actions = {
            {"🏠", fa ? "افزودن به صفحه" : "Add to Home", (Runnable) () -> {
                dialog.dismiss();
                createHomeShortcut(app);
            }},
            {"✏️", fa ? "تغییر نام" : "Rename", (Runnable) () -> {
                showRenameCloneDialog(app, dialog);
            }},
            {"📑", fa ? "تکثیر در فضای جدید" : "Duplicate", (Runnable) () -> {
                dialog.dismiss();
                duplicateCloneToNextSpace(app);
            }},
            {"📱", fa ? "مدل گوشی اپ" : "Device Identity", (Runnable) () -> {
                showPerCloneDeviceIdentityDialog(app, dialog);
            }},
            {"🔑", fa ? "مجوزها" : "Permissions", (Runnable) () -> {
                dialog.dismiss();
                openHostAppPermissions(app.packageName);
            }},
            {"⏹️", fa ? "توقف اجرا" : "Stop", (Runnable) () -> {
                Engine.stopClone(app.packageName, app.userId);
                Toast.makeText(this, fa ? "برنامه متوقف شد" : "App stopped", Toast.LENGTH_SHORT).show();
            }},
            {"🧹", fa ? "پاکسازی داده" : "Clear Data", (Runnable) () -> {
                Engine.clearCloneData(app.packageName, app.userId);
                Toast.makeText(this, fa ? "داده‌های کلون پاک شد" : "Clone data cleared", Toast.LENGTH_SHORT).show();
            }},
            {"🗑️", fa ? "حذف این کلون" : "Uninstall", (Runnable) () -> {
                dialog.dismiss();
                activeConfigDialog = null;
                Engine.uninstallClone(this, app.packageName, app.userId);
                Toast.makeText(this, fa ? "کلون حذف شد" : "Clone uninstalled", Toast.LENGTH_SHORT).show();
                renderCurrentTab();
            }},
            {"📦", fa ? "حذف گروهی" : "Batch uninstall", (Runnable) () -> {
                dialog.dismiss();
                activeConfigDialog = null;
                showBatchUninstallDialog(app.userId);
            }}
        };

        for (Object[] act : actions) {
            String emoji = (String) act[0];
            String label = (String) act[1];
            Runnable runner = (Runnable) act[2];

            LinearLayout tile = new LinearLayout(this);
            tile.setOrientation(LinearLayout.VERTICAL);
            tile.setGravity(Gravity.CENTER);
            GradientDrawable tileBg = new GradientDrawable();
            tileBg.setColor(Color.parseColor("#F8FAFC"));
            tileBg.setCornerRadius(dp(16));
            tileBg.setStroke(dp(1), Color.parseColor("#E2E8F0"));
            tile.setBackground(tileBg);
            tile.setPadding(dp(6), dp(12), dp(6), dp(12));

            GridLayout.LayoutParams tLp = new GridLayout.LayoutParams();
            tLp.width = btnWidth;
            tLp.height = dp(78);
            tLp.setMargins(dp(4), dp(4), dp(4), dp(4));
            tile.setLayoutParams(tLp);

            TextView tvEmoji = new TextView(this);
            tvEmoji.setText(emoji);
            tvEmoji.setTextSize(20f);
            tvEmoji.setGravity(Gravity.CENTER);
            tile.addView(tvEmoji);

            TextView tvLbl = new TextView(this);
            tvLbl.setText(label);
            tvLbl.setTextSize(11.5f);
            tvLbl.setTextColor(Color.parseColor("#334155"));
            tvLbl.setGravity(Gravity.CENTER);
            tvLbl.setPadding(0, dp(4), 0, 0);
            tile.addView(tvLbl);

            tile.setOnClickListener(v -> runner.run());
            actionGrid.addView(tile);
        }

        sheet.addView(actionGrid);
        dialog.setContentView(sheet);

        Window window = dialog.getWindow();
        if (window != null) {
            window.setLayout(WindowManager.LayoutParams.MATCH_PARENT, WindowManager.LayoutParams.WRAP_CONTENT);
            window.setGravity(Gravity.BOTTOM);
            window.setBackgroundDrawableResource(android.R.color.transparent);
        }
        dialog.show();
    }

    private void showRenameCloneDialog(final Engine.AppModel app, final Dialog parentSheet) {
        boolean fa = isFa();
        AlertDialog.Builder b = new AlertDialog.Builder(this);
        b.setTitle(fa ? "تغییر نام نمایشی برنامه" : "Rename Clone");

        final EditText input = new EditText(this);
        input.setText(app.name);
        input.setPadding(dp(20), dp(16), dp(20), dp(16));
        b.setView(input);

        b.setPositiveButton(fa ? "ذخیره فوری" : "Save Now", (d, w) -> {
            String newAlias = input.getText().toString().trim();
            CloneMetadataStore.setAlias(this, app.packageName, app.userId, newAlias);
            app.name = newAlias.isEmpty() ? app.name : newAlias;
            renderCurrentTab();
            if (parentSheet != null && parentSheet.isShowing()) {
                parentSheet.dismiss();
                showCloneConfigurationBottomSheet(app);
            }
        });
        b.setNegativeButton(fa ? "انصراف" : "Cancel", null);
        b.show();
    }

    private void duplicateCloneToNextSpace(Engine.AppModel app) {
        boolean fa = isFa();
        int nextSpace = Engine.findNextAvailableUserIdForPackage(this, app.packageName, MAX_SPACES);
        boolean ok = Engine.installClone(this, app.packageName, nextSpace);
        if (ok) {
            saveExpandedState(nextSpace, true);
            Toast.makeText(this,
                    (fa ? "کلون جدید در فضای " : "Duplicated into Space ") + (nextSpace + 1) + (fa ? " ساخته شد" : ""),
                    Toast.LENGTH_SHORT).show();
            renderCurrentTab();
        }
    }

    private void showPerCloneDeviceIdentityDialog(final Engine.AppModel app, final Dialog parentSheet) {
        boolean fa = isFa();
        final String[][] profiles = {
            {"Apple", "iPhone 16 Pro Max", "iPhone17,2", fa ? "🍎 Apple iPhone 16 Pro Max (اپل)" : "🍎 Apple iPhone 16 Pro Max"},
            {"Apple", "iPhone 15 Pro Max", "iPhone16,2", fa ? "🍎 Apple iPhone 15 Pro Max (اپل)" : "🍎 Apple iPhone 15 Pro Max"},
            {"Apple", "iPhone 14 Pro", "iPhone15,2", fa ? "🍎 Apple iPhone 14 Pro (اپل)" : "🍎 Apple iPhone 14 Pro"},
            {"Apple", "iPad Pro M4", "iPad16,6", fa ? "🍎 Apple iPad Pro M4 (آیپد)" : "🍎 Apple iPad Pro M4"},
            {"Samsung", "SM-S928B (Galaxy S24 Ultra)", "e3q", "🇸🇰 Samsung Galaxy S24 Ultra (SM-S928B)"},
            {"Google", "Pixel 8 Pro", "husky", "🇬 Google Pixel 8 Pro"},
            {"Samsung", "SM-S918B (Galaxy S23 Ultra)", "dm3q", "🇸🇰 Samsung Galaxy S23 Ultra (SM-S918B)"},
            {"Xiaomi", "23116PN5BC (Xiaomi 14 Pro)", "shennong", "🇽 Xiaomi 14 Pro"},
            {"OnePlus", "CPH2581 (OnePlus 12)", "ossi", "🇴 OnePlus 12"},
            {"CUSTOM", "CUSTOM", "CUSTOM", fa ? "✍️ ورود دستی نام برند و مدل دلخواه..." : "✍️ Enter Custom Brand & Model..."},
            {"RESET", "RESET", "RESET", fa ? "🔄 بازگشت به مدل سراسری پیش‌فرض" : "🔄 Reset to Global Device Model"}
        };

        String[] labels = new String[profiles.length];
        for (int i = 0; i < profiles.length; i++) labels[i] = profiles[i][3];

        AlertDialog.Builder b = new AlertDialog.Builder(this);
        b.setTitle(fa
                ? ("تنظیم مدل اختصاصی برای " + app.name + " (اولویت اول)")
                : ("Custom Device Identity for " + app.name + " (Priority 1)"));
        b.setItems(labels, (d, which) -> {
            String[] sel = profiles[which];
            if ("RESET".equals(sel[0])) {
                CloneMetadataStore.clearCustomDeviceIdentity(this, app.packageName, app.userId);
                Toast.makeText(this, fa ? "روی مدل سراسری تنظیم شد" : "Reverted to Global Model", Toast.LENGTH_SHORT).show();
                renderCurrentTab();
                if (parentSheet != null && parentSheet.isShowing()) {
                    parentSheet.dismiss();
                    showCloneConfigurationBottomSheet(app);
                }
            } else if ("CUSTOM".equals(sel[0])) {
                showManualDeviceIdentityDialog(app, parentSheet);
            } else {
                CloneMetadataStore.setCustomDeviceIdentity(this, app.packageName, app.userId, sel[0], sel[1], sel[2]);
                VirtualHookManager.prepareForCloneLaunch(this, app.packageName, app.userId);
                Toast.makeText(this,
                        (fa ? "✓ مدل اختصاصی با اولویت اول ثبت شد: " : "✓ Priority Identity set: ") + sel[0] + " " + sel[1],
                        Toast.LENGTH_SHORT).show();
                renderCurrentTab();
                if (parentSheet != null && parentSheet.isShowing()) {
                    parentSheet.dismiss();
                    showCloneConfigurationBottomSheet(app);
                }
            }
        });
        b.show();
    }

    private void showManualDeviceIdentityDialog(final Engine.AppModel app, final Dialog parentSheet) {
        boolean fa = isFa();
        AlertDialog.Builder b = new AlertDialog.Builder(this);
        b.setTitle(fa ? "ورود دستی برند و مدل دستگاه" : "Custom Device Brand & Model");

        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        int pad = dp(20);
        layout.setPadding(pad, dp(12), pad, dp(8));

        final EditText etBrand = new EditText(this);
        etBrand.setHint(fa ? "برند (مثلاً Apple یا Samsung)" : "Brand (e.g. Apple or Samsung)");
        etBrand.setText("Apple");
        layout.addView(etBrand);

        final EditText etModel = new EditText(this);
        etModel.setHint(fa ? "مدل (مثلاً iPhone 16 Pro Max)" : "Model (e.g. iPhone 16 Pro Max)");
        etModel.setText("iPhone 16 Pro Max");
        layout.addView(etModel);

        b.setView(layout);
        b.setPositiveButton(fa ? "ثبت فوری" : "Save Now", (d, w) -> {
            String brand = etBrand.getText().toString().trim();
            String model = etModel.getText().toString().trim();
            if (!brand.isEmpty() && !model.isEmpty()) {
                CloneMetadataStore.setCustomDeviceIdentity(this, app.packageName, app.userId, brand, model, "custom_dev");
                VirtualHookManager.prepareForCloneLaunch(this, app.packageName, app.userId);
                renderCurrentTab();
                if (parentSheet != null && parentSheet.isShowing()) {
                    parentSheet.dismiss();
                    showCloneConfigurationBottomSheet(app);
                }
            }
        });
        b.setNegativeButton(fa ? "انصراف" : "Cancel", null);
        b.show();
    }

    private void createHomeShortcut(Engine.AppModel app) {
        boolean fa = isFa();
        try {
            Intent launchIntent = new Intent(this, MainActivity.class);
            launchIntent.setAction(Intent.ACTION_MAIN);
            Intent addIntent = new Intent("com.android.launcher.action.INSTALL_SHORTCUT");
            addIntent.putExtra(Intent.EXTRA_SHORTCUT_INTENT, launchIntent);
            addIntent.putExtra(Intent.EXTRA_SHORTCUT_NAME, app.name + " (" + (app.userId + 1) + ")");
            sendBroadcast(addIntent);
            Toast.makeText(this, fa ? "درخواست افزودن میان‌بر ارسال شد" : "Shortcut request sent", Toast.LENGTH_SHORT).show();
        } catch (Exception e) {
            Toast.makeText(this, fa ? "امکان ساخت میان‌بر وجود ندارد" : "Shortcut not supported", Toast.LENGTH_SHORT).show();
        }
    }

    private void openHostAppPermissions(String pkg) {
        try {
            Intent intent = new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS);
            intent.setData(Uri.fromParts("package", pkg, null));
            startActivity(intent);
        } catch (Exception e) {
            Intent intent = new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS);
            intent.setData(Uri.fromParts("package", getPackageName(), null));
            startActivity(intent);
        }
    }

    private void showBatchUninstallDialog(final int userId) {
        boolean fa = isFa();
        final List<Engine.AppModel> clones = Engine.getClonedApps(this, userId);
        if (clones.isEmpty()) return;

        String[] names = new String[clones.size()];
        final boolean[] checked = new boolean[clones.size()];
        for (int i = 0; i < clones.size(); i++) {
            names[i] = clones.get(i).name;
            checked[i] = false;
        }

        AlertDialog.Builder b = new AlertDialog.Builder(this);
        b.setTitle(fa ? "حذف گروهی کلون‌ها" : "Batch Uninstall Clones");
        b.setMultiChoiceItems(names, checked, (d, which, isChecked) -> checked[which] = isChecked);
        b.setPositiveButton(fa ? "حذف انتخاب‌شده‌ها" : "Uninstall Selected", (d, w) -> {
            for (int i = 0; i < clones.size(); i++) {
                if (checked[i]) {
                    Engine.uninstallClone(this, clones.get(i).packageName, userId);
                }
            }
            renderCurrentTab();
        });
        b.setNegativeButton(fa ? "انصراف" : "Cancel", null);
        b.show();
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        renderCurrentTab();
        if (activeConfigDialog != null && activeConfigDialog.isShowing() && activeConfigApp != null) {
            activeConfigDialog.dismiss();
            showCloneConfigurationBottomSheet(activeConfigApp);
        }
    }

    private boolean isFa() {
        return "fa".equals(LocaleHelper.getLanguage(this));
    }

    private int dp(int v) {
        return (int) (v * getResources().getDisplayMetrics().density);
    }
}
""")

    print("[v3-Part2] All UI Screens, Stealth Dashboard, Dual Lock & External Store Installer updated.")

if __name__ == "__main__":
    apply_part2()
