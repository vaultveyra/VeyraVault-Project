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
import com.veyravault.space.core.CloneStore;
import com.veyravault.space.core.LocaleHelper;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.TimeZone;

public class DashboardActivity extends BaseActivity {
    private int dp(int n) { return (int)(n * getResources().getDisplayMetrics().density + 0.5f); }
    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        final boolean fa = LocaleHelper.isPersian(this);
        List<CloneStore.CloneEntry> clones = CloneStore.getAll(this);
        Set<Integer> spaces = new HashSet<Integer>();
        for (CloneStore.CloneEntry clone : clones) spaces.add(clone.getSpaceNumber());
        ScrollView scroll = new ScrollView(this);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(24),dp(28),dp(24),dp(32));
        root.setBackgroundColor(Color.rgb(243,245,249));
        scroll.addView(root);
        TextView title = new TextView(this);
        title.setText("VeyraVault"); title.setTextSize(26); title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setTextColor(Color.rgb(17,24,39)); root.addView(title);
        TextView subtitle = new TextView(this);
        subtitle.setText(fa ? "مرکز مدیریت فضاهای شما" : "Your multi-space control center");
        subtitle.setTextSize(14); subtitle.setTextColor(Color.rgb(107,114,128));
        subtitle.setPadding(0,dp(6),0,dp(20)); root.addView(subtitle);
        LinearLayout stats = new LinearLayout(this);
        stats.setOrientation(LinearLayout.HORIZONTAL);
        stats.addView(statCard(fa ? "کلون‌ها" : "Clones", String.valueOf(clones.size())), new LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1));
        LinearLayout.LayoutParams second = new LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1);
        second.setMargins(dp(10),0,0,0);
        stats.addView(statCard(fa ? "فضاهای استفاده‌شده" : "Spaces used", String.valueOf(spaces.size())), second);
        root.addView(stats);
        addAction(root,fa ? "مدیریت فضاها" : "Manage Spaces",fa ? "مشاهده و اجرای کلون‌های موجود" : "View and launch your existing clones",new View.OnClickListener(){@Override public void onClick(View v){startActivity(new Intent(DashboardActivity.this,MainActivity.class));finish();}});
        addAction(root,fa ? "افزودن برنامه" : "Add an App",fa ? "ساخت کلون جدید در یک فضای مستقل" : "Create a clone in an independent space",new View.OnClickListener(){@Override public void onClick(View v){startActivity(new Intent(DashboardActivity.this,AddAppActivity.class));}});
        addAction(root,"VPN",fa ? "وضعیت VPN سیستم و قابلیت فعلی برنامه" : "System VPN status and current app capability",new View.OnClickListener(){@Override public void onClick(View v){startActivity(new Intent(DashboardActivity.this,VpnStatusActivity.class));}});
        addAction(root,fa ? "تنظیمات" : "Settings",fa ? "زبان، محیط سراسری، امنیت و گزارش سازگاری" : "Language, global environment, security and diagnostics",new View.OnClickListener(){@Override public void onClick(View v){startActivity(new Intent(DashboardActivity.this,SettingsHubActivity.class));}});
        TextView zone = new TextView(this);
        zone.setText((fa ? "منطقه زمانی دستگاه: " : "Device time zone: ") + TimeZone.getDefault().getID());
        zone.setTextSize(12); zone.setTextColor(Color.rgb(107,114,128)); zone.setPadding(0,dp(18),0,0); root.addView(zone);
        setContentView(scroll);
    }
    private View statCard(String label,String value) {
        LinearLayout card=new LinearLayout(this); card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(16),dp(18),dp(16),dp(18)); card.setBackgroundResource(com.veyravault.space.R.drawable.bg_card_rounded);
        TextView number=new TextView(this); number.setText(value); number.setTextSize(25); number.setTypeface(Typeface.DEFAULT_BOLD); number.setTextColor(Color.rgb(37,99,235)); card.addView(number);
        TextView caption=new TextView(this); caption.setText(label); caption.setTextSize(12); caption.setTextColor(Color.rgb(75,85,99)); card.addView(caption); return card;
    }
    private void addAction(LinearLayout root,String heading,String detail,View.OnClickListener click) {
        LinearLayout card=new LinearLayout(this); card.setOrientation(LinearLayout.VERTICAL); card.setPadding(dp(18),dp(16),dp(18),dp(16));
        card.setBackgroundResource(com.veyravault.space.R.drawable.bg_card_rounded);
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT); lp.topMargin=dp(12);
        TextView h=new TextView(this); h.setText(heading); h.setTextSize(16); h.setTypeface(Typeface.DEFAULT_BOLD); h.setTextColor(Color.rgb(31,41,55)); card.addView(h);
        TextView d=new TextView(this); d.setText(detail); d.setTextSize(12); d.setTextColor(Color.rgb(107,114,128)); d.setPadding(0,dp(5),0,0); card.addView(d);
        card.setOnClickListener(click); root.addView(card,lp);
    }
}