package com.veyravault.space.ui;

import android.content.Context;
import android.graphics.Color;
import android.graphics.Typeface;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.os.Build;
import android.os.Bundle;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.TextView;
import com.veyravault.space.core.LocaleHelper;

public class VpnStatusActivity extends BaseActivity {
    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        boolean fa=LocaleHelper.isPersian(this), active=isSystemVpnActive();
        LinearLayout root=new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setPadding(48,48,48,48); root.setBackgroundColor(UiPalette.page(getApplicationContext()));
        TextView title=new TextView(this); title.setText(fa ? "وضعیت VPN" : "VPN Status"); title.setTextSize(23); title.setTypeface(Typeface.DEFAULT_BOLD); title.setTextColor(UiPalette.textPrimary(getApplicationContext())); root.addView(title);
        TextView status=new TextView(this);
        status.setText(active ? (fa ? "یک انتقال شبکه VPN در سطح سیستم شناسایی شد." : "A system-level VPN network transport is currently detected.") : (fa ? "انتقال شبکه VPN فعال شناسایی نشد." : "No active system VPN transport was detected."));
        status.setTextSize(15); status.setTextColor(active?Color.rgb(5,100,70):UiPalette.textSecondary(getApplicationContext())); status.setPadding(0,32,0,20); root.addView(status);
        TextView note=new TextView(this);
        note.setText(fa ? "شفاف‌سازی: در نسخه فعلی، سرویس VPN اختصاصی VeyraVault و اتصال به سرور VPN پیاده‌سازی نشده است. این صفحه فقط وضعیت انتقال VPN سیستم اندروید را به‌صورت خواندنی گزارش می‌کند و هیچ اتصال یا تنظیم شبکه‌ای را تغییر نمی‌دهد." : "Transparency: this version does not implement a dedicated VeyraVault VPN service or VPN server connection. This page only reports Android's system VPN transport state; it does not create a connection or change network settings.");
        note.setTextSize(14); note.setTextColor(UiPalette.textSecondary(getApplicationContext())); root.addView(note,new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT));
        setContentView(root);
    }
    private boolean isSystemVpnActive() {
        if(Build.VERSION.SDK_INT<23) return false;
        try { ConnectivityManager cm=(ConnectivityManager)getSystemService(Context.CONNECTIVITY_SERVICE); if(cm==null)return false;
            for(Network n:cm.getAllNetworks()){NetworkCapabilities c=cm.getNetworkCapabilities(n);if(c!=null&&c.hasTransport(NetworkCapabilities.TRANSPORT_VPN))return true;}
        } catch(SecurityException ignored) {}
        return false;
    }
}