package com.veyravault.space.ui;

import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import androidx.appcompat.app.AppCompatActivity;
import com.veyravault.space.core.LocaleHelper;
import com.veyravault.space.security.SecurityManager;

public abstract class BaseActivity extends AppCompatActivity {
    @Override
    protected void attachBaseContext(Context newBase) {
        super.attachBaseContext(LocaleHelper.applyLocale(newBase));
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        LocaleHelper.applyLocale(this);
        super.onCreate(savedInstanceState);
        if (Build.VERSION.SDK_INT >= 17) {
            getWindow().getDecorView().setLayoutDirection(
                    LocaleHelper.isPersian(this) ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR
            );
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (!(this instanceof SecurityLockActivity) && !SecurityManager.isSessionUnlocked(this)) {
            startActivity(new Intent(this, SecurityLockActivity.class));
        }
    }
}
