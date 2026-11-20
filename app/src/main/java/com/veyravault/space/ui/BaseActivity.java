package com.veyravault.space.ui;

import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import com.veyravault.space.core.LocaleHelper;
import com.veyravault.space.core.AppearanceManager;
import com.veyravault.space.security.SecurityManager;

public abstract class BaseActivity extends AppCompatActivity {
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


    /** Lock action for primary app headers. It reuses the existing authenticated lock screen. */
    protected TextView createImmediateLockAction(boolean fa) {
        TextView action = new TextView(this);
        action.setText(fa ? "قفل فوری" : "Lock");
        action.setTextSize(13f);
        action.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
        action.setTextColor(UiPalette.accent(this));
        action.setBackgroundResource(com.veyravault.space.R.drawable.bg_pill_lightblue);
        action.setGravity(android.view.Gravity.CENTER);
        action.setPadding(dp(14), dp(9), dp(14), dp(9));
        action.setContentDescription(fa ? "قفل فوری برنامه" : "Lock VeyraVault now");
        action.setOnClickListener(view -> {
            if (!SecurityManager.isLockEnabled(this)) {
                Toast.makeText(this,
                        fa ? "ابتدا PIN یا Pattern را در بخش امنیت تنظیم کنید."
                           : "Set a PIN or Pattern in Security Settings before locking.",
                        Toast.LENGTH_LONG).show();
                startActivity(new Intent(this, SecuritySettingsActivity.class));
                return;
            }
            SecurityManager.lockSession();
            Intent lock = new Intent(this, SecurityLockActivity.class);
            lock.addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP);
            startActivity(lock);
        });
        return action;
    }

    protected int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (!(this instanceof SecurityLockActivity) && !SecurityManager.isSessionUnlocked(this)) {
            startActivity(new Intent(this, SecurityLockActivity.class));
        }
    }
}
