package com.veyravault.space.ui;

import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
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
        boolean fa = LocaleHelper.isPersian(this);

        ScrollView sv = new ScrollView(this);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(48, 48, 48, 48);
        sv.addView(root);

        TextView title = new TextView(this);
        title.setText("VeyraVault v2.0 Enterprise");
        title.setTextSize(22f);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setTextColor(Color.parseColor("#2563EB"));
        root.addView(title);

        TextView body = new TextView(this);
        body.setTextSize(14f);
        body.setTextColor(Color.parseColor("#374151"));
        body.setPadding(0, 24, 0, 32);
        body.setText(fa
                ? "برنامه شخصی، امن و بدون تبلیغات برای ساخت فضاهای مجازی چندگانه (Clones)، مدیریت موقعیت مکانی مجزا برای هر برنامه، مدیریت هویت دستگاه، پشتیبانی از گوگل‌پلی (GMS)، تغییر آیکون و محافظت در برابر حذف.\n\n"
                  + "• بدون هیچ‌گونه سرور خارجی، تبلیغات یا ردیاب\n"
                  + "• ذخیره ۱۰۰٪ اطلاعات فقط روی حافظه داخلی دستگاه شما\n"
                  + "• مبتنی بر موتور متن‌باز BlackBox (مجوز Apache-2.0)\n\n"
                  + "ارتباط با سازنده:\n"
                  + "Email: Vaultveyra@gmail.com\n"
                  + "Telegram: https://t.me/VaultVeyra"
                : "Private, zero-telemetry Android multi-space virtualization app with per-clone Mock GPS, per-clone & global device identity profiles, GMS support, icon disguise, and anti-uninstall protection.\n\n"
                  + "Contact:\nEmail: Vaultveyra@gmail.com\nTelegram: https://t.me/VaultVeyra");
        root.addView(body);

        Button tgBtn = new Button(this);
        tgBtn.setBackgroundResource(R.drawable.bg_pill_blue);
        tgBtn.setTextColor(Color.WHITE);
        tgBtn.setAllCaps(false);
        tgBtn.setText("Telegram: @VaultVeyra");
        tgBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse("https://t.me/VaultVeyra")));
            }
        });
        root.addView(tgBtn);

        setContentView(sv);
    }
}
