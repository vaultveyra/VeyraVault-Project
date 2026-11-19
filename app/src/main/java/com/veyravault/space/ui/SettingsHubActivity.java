package com.veyravault.space.ui;

import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import com.veyravault.space.core.LocaleHelper;

public class SettingsHubActivity extends BaseActivity {
    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        final boolean fa=LocaleHelper.isPersian(this);
        ScrollView scroll=new ScrollView(this); LinearLayout root=new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setPadding(40,40,40,48); root.setBackgroundColor(Color.rgb(243,245,249)); scroll.addView(root);
        TextView title=new TextView(this); title.setText(fa?"تنظیمات":"Settings"); title.setTextSize(24); title.setTypeface(Typeface.DEFAULT_BOLD); title.setTextColor(Color.rgb(17,24,39)); root.addView(title);
        addRow(root,fa?"محیط و پروفایل سراسری":"Global Environment",fa?"مدیریت تنظیمات عمومی محیط":"Manage global environment preferences",GlobalEnvironmentActivity.class);
        addRow(root,fa?"امنیت و قفل برنامه":"Security & App Lock",fa?"مدیریت قفل و گزینه‌های امنیتی":"Manage app lock and security options",SecuritySettingsActivity.class);
        addRow(root,fa?"مجوزها و شفافیت":"Permissions & Transparency",fa?"مشاهده وضعیت مجوزهای برنامه":"Review app permission status",PermissionsActivity.class);
        addRow(root,fa?"درباره برنامه و گزارش سازگاری":"About & Compatibility",fa?"اطلاعات نسخه و عیب‌یابی خواندنی":"Version information and read-only diagnostics",AboutActivity.class);
        addRow(root,fa?"بررسی رزروهای معلق":"Pending Clone ID reservations",fa?"بررسی وضعیت موتور و آزادسازی دستی شناسه‌های امن":"Inspect Engine state and manually release only confirmed-absent reservations",PendingReservationsActivity.class);
        addFutureBackupSection(root, fa);
        LinearLayout language=new LinearLayout(this); language.setOrientation(LinearLayout.VERTICAL); language.setPadding(28,24,28,24); language.setBackgroundResource(com.veyravault.space.R.drawable.bg_card_rounded);
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT); lp.topMargin=20;
        TextView label=new TextView(this); label.setText(fa?"زبان برنامه":"App Language"); label.setTextSize(16); label.setTypeface(Typeface.DEFAULT_BOLD); label.setTextColor(Color.rgb(31,41,55)); language.addView(label);
        TextView toggle=new TextView(this); toggle.setText(fa?"Switch to English":"تغییر به فارسی"); toggle.setTextSize(14); toggle.setTextColor(Color.rgb(37,99,235)); toggle.setPadding(0,16,0,0);
        toggle.setOnClickListener(new View.OnClickListener(){@Override public void onClick(View v){LocaleHelper.toggleLanguage(SettingsHubActivity.this);recreate();}});
        language.addView(toggle); root.addView(language,lp); setContentView(scroll);
    }
    private void addFutureBackupSection(LinearLayout root, boolean fa) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(28, 24, 28, 24);
        card.setBackgroundResource(com.veyravault.space.R.drawable.bg_card_rounded);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        lp.topMargin = 18;

        TextView heading = new TextView(this);
        heading.setText(fa ? "پشتیبان‌گیری و بازیابی داده‌ها" : "Backup & Restore");
        heading.setTextSize(16);
        heading.setTypeface(Typeface.DEFAULT_BOLD);
        heading.setTextColor(Color.rgb(31, 41, 55));
        card.addView(heading);

        TextView detail = new TextView(this);
        detail.setText(fa
                ? "محل این قابلیت برای توسعه آینده رزرو شده است. هنوز هیچ نسخه پشتیبان یا بازیابی انجام نمی‌شود و داده‌ای تغییر نمی‌کند."
                : "Reserved for a future release. Backup and restore are not active yet; no data is read, written, exported or restored.");
        detail.setTextSize(12);
        detail.setTextColor(Color.rgb(107, 114, 128));
        detail.setPadding(0, 6, 0, 0);
        card.addView(detail);
        root.addView(card, lp);
    }

    private void addRow(LinearLayout root,String heading,String detail,final Class<?> target) {
        LinearLayout card=new LinearLayout(this); card.setOrientation(LinearLayout.VERTICAL); card.setPadding(28,24,28,24); card.setBackgroundResource(com.veyravault.space.R.drawable.bg_card_rounded);
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT); lp.topMargin=18;
        TextView h=new TextView(this); h.setText(heading); h.setTextSize(16); h.setTypeface(Typeface.DEFAULT_BOLD); h.setTextColor(Color.rgb(31,41,55)); card.addView(h);
        TextView d=new TextView(this); d.setText(detail); d.setTextSize(12); d.setTextColor(Color.rgb(107,114,128)); d.setPadding(0,6,0,0); card.addView(d);
        card.setOnClickListener(new View.OnClickListener(){@Override public void onClick(View v){startActivity(new Intent(SettingsHubActivity.this,target));}}); root.addView(card,lp);
    }
}