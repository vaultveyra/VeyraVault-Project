package com.veyravault.space.ui;

import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.os.Build;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.TextClock;
import com.veyravault.space.core.AsyncCloneRepository;
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
        final TextView cloneCount = (TextView) ((LinearLayout) statCard(fa ? "کلون‌ها" : "Clones", "…")).getChildAt(0);
        LinearLayout cloneCard = (LinearLayout) cloneCount.getParent();
        stats.addView(cloneCard, new LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1));
        final TextView spaceCount = (TextView) ((LinearLayout) statCard(fa ? "فضاهای استفاده‌شده" : "Spaces used", "…")).getChildAt(0);
        LinearLayout spaceCard = (LinearLayout) spaceCount.getParent();
        LinearLayout.LayoutParams second = new LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1);
        second.setMargins(dp(10),0,0,0);
        stats.addView(spaceCard, second);
        root.addView(stats);

        // Live city clocks use Android TextClock and explicit IANA time zones.
        LinearLayout clocks = new LinearLayout(this);
        clocks.setOrientation(LinearLayout.HORIZONTAL);
        clocks.setPadding(0, dp(14), 0, dp(4));
        clocks.addView(clockCard(fa ? "تهران" : "Tehran", "Asia/Tehran", fa),
                new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        LinearLayout.LayoutParams nyLp = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f);
        nyLp.setMargins(dp(10), 0, 0, 0);
        clocks.addView(clockCard(fa ? "نیویورک" : "New York", "America/New_York", fa), nyLp);
        root.addView(clocks);

        TextView deviceInfo = new TextView(this);
        deviceInfo.setText((fa ? "دستگاه: " : "Device: ") + Build.MANUFACTURER + " " + Build.MODEL
                + "  •  Android " + Build.VERSION.RELEASE);
        deviceInfo.setTextSize(12);
        deviceInfo.setTextColor(Color.rgb(75,85,99));
        deviceInfo.setPadding(0, dp(12), 0, dp(4));
        root.addView(deviceInfo);

        final TextView registryStatus = new TextView(this);
        registryStatus.setTextSize(12);
        registryStatus.setTextColor(Color.rgb(185,28,28));
        registryStatus.setPadding(0,dp(8),0,0);
        registryStatus.setVisibility(View.GONE);
        root.addView(registryStatus);
        AsyncCloneRepository.getInstance(getApplicationContext()).loadClones(
                new AsyncCloneRepository.Callback<List<CloneStore.CloneEntry>>() {
                    @Override public void onComplete(AsyncCloneRepository.Result<List<CloneStore.CloneEntry>> result) {
                        if (isFinishing() || isDestroyed()) return;
                        if (!result.isSuccess() || result.getValue() == null) {
                            cloneCount.setText("—");
                            spaceCount.setText("—");
                            registryStatus.setText(fa
                                    ? "خواندن فهرست فضاها ناموفق بود؛ آمار نمایش‌داده نمی‌شود."
                                    : "Could not validate the Space registry; counts are unavailable.");
                            registryStatus.setVisibility(View.VISIBLE);
                            return;
                        }
                        Set<Integer> spaces = new HashSet<Integer>();
                        for (CloneStore.CloneEntry clone : result.getValue()) spaces.add(clone.getSpaceNumber());
                        cloneCount.setText(String.valueOf(result.getValue().size()));
                        spaceCount.setText(String.valueOf(spaces.size()));
                    }
                });
        addAction(root,fa ? "مدیریت فضاها" : "Manage Spaces",fa ? "مشاهده و اجرای کلون‌های موجود" : "View and launch your existing clones",new View.OnClickListener(){@Override public void onClick(View v){startActivity(new Intent(DashboardActivity.this,MainActivity.class));finish();}});
        addAction(root,fa ? "افزودن برنامه" : "Add an App",fa ? "ساخت کلون جدید در یک فضای مستقل" : "Create a clone in an independent space",new View.OnClickListener(){@Override public void onClick(View v){startActivity(new Intent(DashboardActivity.this,AddAppActivity.class));}});
        addAction(root,"VPN",fa ? "وضعیت VPN سیستم و قابلیت فعلی برنامه" : "System VPN status and current app capability",new View.OnClickListener(){@Override public void onClick(View v){startActivity(new Intent(DashboardActivity.this,VpnStatusActivity.class));}});
        addAction(root,fa ? "تنظیمات" : "Settings",fa ? "زبان، محیط سراسری، امنیت و گزارش سازگاری" : "Language, global environment, security and diagnostics",new View.OnClickListener(){@Override public void onClick(View v){startActivity(new Intent(DashboardActivity.this,SettingsHubActivity.class));}});
        TextView zone = new TextView(this);
        zone.setText((fa ? "منطقه زمانی دستگاه: " : "Device time zone: ") + TimeZone.getDefault().getID());
        zone.setTextSize(12); zone.setTextColor(Color.rgb(107,114,128)); zone.setPadding(0,dp(18),0,0); root.addView(zone);
        setContentView(scroll);
    }
    private View clockCard(String city, String zoneId, boolean fa) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(14), dp(14), dp(14), dp(14));
        card.setBackgroundResource(com.veyravault.space.R.drawable.bg_card_rounded);
        TextView label = new TextView(this);
        label.setText(city);
        label.setTextSize(12);
        label.setTypeface(Typeface.DEFAULT_BOLD);
        label.setTextColor(Color.rgb(75,85,99));
        card.addView(label);
        TextClock clock = new TextClock(this);
        clock.setFormat24Hour("HH:mm:ss");
        clock.setFormat12Hour("hh:mm:ss a");
        clock.setTimeZone(zoneId);
        clock.setTextSize(25);
        clock.setTypeface(Typeface.DEFAULT_BOLD);
        clock.setTextColor(Color.rgb(37,99,235));
        clock.setPadding(0, dp(5), 0, 0);
        card.addView(clock);
        TextView zone = new TextView(this);
        zone.setText(zoneId);
        zone.setTextSize(10);
        zone.setTextColor(Color.rgb(107,114,128));
        card.addView(zone);
        return card;
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
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