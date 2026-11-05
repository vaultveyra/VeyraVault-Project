package com.veyravault.space.ui;

import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import com.veyravault.space.R;
import com.veyravault.space.core.LocaleHelper;
import com.veyravault.space.security.SecurityManager;

public class SecurityLockActivity extends BaseActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        final boolean fa = LocaleHelper.isPersian(this);
        final int setupMode = getIntent().getIntExtra("setup_mode", -1);
        final int mode = setupMode != -1 ? setupMode : SecurityManager.getLockMode(this);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        root.setBackgroundColor(Color.parseColor("#1E293B"));
        root.setPadding(64, 64, 64, 64);

        TextView title = new TextView(this);
        title.setTextColor(Color.WHITE);
        title.setTextSize(22f);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setGravity(Gravity.CENTER);
        title.setText(setupMode != -1
                ? (fa ? "ثبت قفل امنیتی جدید" : "Set New Security Lock")
                : (fa ? "قفل امنیتی VeyraVault" : "VeyraVault Security Lock"));
        root.addView(title);

        final TextView sub = new TextView(this);
        sub.setTextColor(Color.parseColor("#94A3B8"));
        sub.setTextSize(14f);
        sub.setGravity(Gravity.CENTER);
        sub.setPadding(0, 16, 0, 48);
        sub.setText(mode == SecurityManager.MODE_PATTERN
                ? (fa ? "الگوی امنیتی خود را رسم کنید (حداقل ۴ نقطه)" : "Draw your security pattern (min 4 dots)")
                : (fa ? "رمز پین عددی خود را وارد کنید" : "Enter your numeric PIN code"));
        root.addView(sub);

        if (mode == SecurityManager.MODE_PATTERN) {
            final PatternLockView patternView = new PatternLockView(this);
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(720, 720);
            root.addView(patternView, lp);
            patternView.setOnPatternListener(new PatternLockView.OnPatternListener() {
                @Override
                public void onPatternComplete(String patternString) {
                    if (patternString.length() < 4) {
                        Toast.makeText(SecurityLockActivity.this, fa ? "حداقل ۴ نقطه را وصل کنید" : "Connect at least 4 dots", Toast.LENGTH_SHORT).show();
                        patternView.clearPattern();
                        return;
                    }
                    if (setupMode != -1) {
                        SecurityManager.setLockCredential(SecurityLockActivity.this, SecurityManager.MODE_PATTERN, patternString);
                        Toast.makeText(SecurityLockActivity.this, fa ? "الگوی امنیتی ذخیره شد" : "Pattern lock saved", Toast.LENGTH_SHORT).show();
                        finish();
                    } else if (SecurityManager.verifyCredential(SecurityLockActivity.this, patternString)) {
                        finish();
                    } else {
                        Toast.makeText(SecurityLockActivity.this, fa ? "الگو اشتباه است!" : "Incorrect pattern!", Toast.LENGTH_SHORT).show();
                        patternView.clearPattern();
                    }
                }
            });
        } else {
            final EditText pinInput = new EditText(this);
            pinInput.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_VARIATION_PASSWORD);
            pinInput.setTextColor(Color.WHITE);
            pinInput.setHintTextColor(Color.GRAY);
            pinInput.setHint("••••");
            pinInput.setGravity(Gravity.CENTER);
            pinInput.setTextSize(26f);
            root.addView(pinInput);

            Button btn = new Button(this);
            btn.setBackgroundResource(R.drawable.bg_pill_blue);
            btn.setTextColor(Color.WHITE);
            btn.setText(setupMode != -1 ? (fa ? "ذخیره رمز پین" : "Save PIN") : (fa ? "بازگشایی قفل" : "Unlock"));
            LinearLayout.LayoutParams blp = new LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
            blp.topMargin = 36;
            root.addView(btn, blp);

            btn.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    String pin = pinInput.getText().toString().trim();
                    if (pin.length() < 4) {
                        Toast.makeText(SecurityLockActivity.this, fa ? "حداقل ۴ رقم وارد کنید" : "Enter at least 4 digits", Toast.LENGTH_SHORT).show();
                        return;
                    }
                    if (setupMode != -1) {
                        SecurityManager.setLockCredential(SecurityLockActivity.this, SecurityManager.MODE_PIN, pin);
                        Toast.makeText(SecurityLockActivity.this, fa ? "رمز پین فعال شد" : "PIN lock enabled", Toast.LENGTH_SHORT).show();
                        finish();
                    } else if (SecurityManager.verifyCredential(SecurityLockActivity.this, pin)) {
                        finish();
                    } else {
                        Toast.makeText(SecurityLockActivity.this, fa ? "رمز اشتباه است!" : "Wrong PIN!", Toast.LENGTH_SHORT).show();
                    }
                }
            });
        }
        setContentView(root);
    }

    @Override
    public void onBackPressed() {
        if (getIntent().getIntExtra("setup_mode", -1) != -1) {
            super.onBackPressed();
        } else {
            moveTaskToBack(true);
        }
    }
}
