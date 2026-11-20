package com.veyravault.space.ui;

import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.SwitchCompat;
import com.veyravault.space.core.LocaleHelper;
import com.veyravault.space.core.AppearanceManager;
import com.veyravault.space.security.SecurityManager;

public abstract class BaseActivity extends AppCompatActivity {
    private SwitchCompat immediateLockSwitch;
    private boolean updatingImmediateLockSwitch;
    @Override
    protected void attachBaseContext(Context newBase) {
        super.attachBaseContext(LocaleHelper.applyLocale(newBase));
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        AppearanceManager.apply(this);
        LocaleHelper.applyLocale(this);
        super.onCreate(savedInstanceState);
        if (Build.VERSION.SDK_INT >= 17) {
            getWindow().getDecorView().setLayoutDirection(
                    LocaleHelper.isPersian(this) ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR
            );
        }
    }


    /** Language action shared by primary screen headers. */
    protected TextView createLanguageAction(boolean fa) {
        TextView action = new TextView(this);
        action.setText(getString(com.veyravault.space.R.string.lang_switch));
        action.setTextSize(12f);
        action.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
        action.setTextColor(UiPalette.accent(this));
        action.setBackgroundResource(com.veyravault.space.R.drawable.bg_pill_lightblue);
        action.setGravity(android.view.Gravity.CENTER);
        action.setPadding(lockActionDp(10), lockActionDp(8), lockActionDp(10), lockActionDp(8));
        action.setContentDescription(fa ? "تغییر زبان برنامه" : "Change app language");
        action.setOnClickListener(view -> {
            LocaleHelper.toggleLanguage(BaseActivity.this);
            recreate();
        });
        return action;
    }

    /**
     * A real, stateful lock switch. ON means the app session is locked; OFF means
     * the authenticated session is open. Turning it OFF never authenticates or
     * bypasses PIN/Pattern verification.
     */
    protected SwitchCompat createImmediateLockSwitch(boolean fa) {
        SwitchCompat toggle = new SwitchCompat(this);
        toggle.setTextOn(fa ? "قفل" : "Locked");
        toggle.setTextOff(fa ? "باز" : "Open");
        toggle.setShowText(true);
        toggle.setTextSize(12f);
        toggle.setTextColor(UiPalette.textPrimary(this));
        toggle.setContentDescription(fa
                ? "قفل فوری؛ روشن کردن برای قفل کردن برنامه"
                : "Quick Lock; turn on to lock the app");
        toggle.setChecked(SecurityManager.isLockEnabled(this)
                && !SecurityManager.isSessionUnlocked(this));
        immediateLockSwitch = toggle;
        toggle.setOnCheckedChangeListener((buttonView, isChecked) -> {
            if (updatingImmediateLockSwitch) return;

            if (!isChecked) {
                // The switch cannot unlock. Only SecurityLockActivity can verify credentials.
                setImmediateLockSwitchChecked(SecurityManager.isLockEnabled(BaseActivity.this)
                        && !SecurityManager.isSessionUnlocked(BaseActivity.this));
                if (!SecurityManager.isSessionUnlocked(BaseActivity.this)) {
                    Toast.makeText(BaseActivity.this,
                            fa ? "برای باز کردن قفل، PIN یا Pattern را وارد کنید."
                               : "Enter your PIN or Pattern to unlock.",
                            Toast.LENGTH_LONG).show();
                }
                return;
            }

            if (!SecurityManager.isLockEnabled(BaseActivity.this)) {
                setImmediateLockSwitchChecked(false);
                Toast.makeText(BaseActivity.this,
                        fa ? "ابتدا PIN یا Pattern را در بخش امنیت تنظیم کنید."
                           : "Set a PIN or Pattern in Security Settings before locking.",
                        Toast.LENGTH_LONG).show();
                startActivity(new Intent(BaseActivity.this, SecuritySettingsActivity.class));
                return;
            }

            SecurityManager.lockSession();
            setImmediateLockSwitchChecked(true);
            Intent lock = new Intent(BaseActivity.this, SecurityLockActivity.class);
            lock.addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP);
            startActivity(lock);
        });
        return toggle;
    }

    private void setImmediateLockSwitchChecked(boolean checked) {
        if (immediateLockSwitch == null) return;
        updatingImmediateLockSwitch = true;
        immediateLockSwitch.setChecked(checked);
        updatingImmediateLockSwitch = false;
    }

    private int lockActionDp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    @Override
    protected void onResume() {
        super.onResume();
        setImmediateLockSwitchChecked(SecurityManager.isLockEnabled(this)
                && !SecurityManager.isSessionUnlocked(this));
        if (!(this instanceof SecurityLockActivity) && !SecurityManager.isSessionUnlocked(this)) {
            startActivity(new Intent(this, SecurityLockActivity.class));
        }
    }
}
