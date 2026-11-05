package com.veyravault.space.core;

import android.content.Context;
import android.content.SharedPreferences;
import android.content.res.Configuration;
import android.content.res.Resources;
import android.os.Build;
import java.util.Locale;

public class LocaleHelper {
    private static final String PREF = "veyra_locale_pref";
    private static final String KEY_LANG = "app_lang";

    public static String getLang(Context ctx) {
        SharedPreferences sp = ctx.getSharedPreferences(PREF, Context.MODE_PRIVATE);
        return sp.getString(KEY_LANG, "fa"); // Default Persian (Farsi RTL)
    }

    public static boolean isPersian(Context ctx) {
        return "fa".equalsIgnoreCase(getLang(ctx));
    }

    public static void toggleLanguage(Context ctx) {
        String next = isPersian(ctx) ? "en" : "fa";
        ctx.getSharedPreferences(PREF, Context.MODE_PRIVATE).edit().putString(KEY_LANG, next).apply();
        applyLocale(ctx);
    }

    public static Context applyLocale(Context context) {
        String lang = getLang(context);
        Locale locale = new Locale(lang);
        Locale.setDefault(locale);
        Resources res = context.getResources();
        Configuration config = new Configuration(res.getConfiguration());
        if (Build.VERSION.SDK_INT >= 17) {
            config.setLocale(locale);
            config.setLayoutDirection(locale);
        } else {
            config.locale = locale;
        }
        res.updateConfiguration(config, res.getDisplayMetrics());
        return context;
    }
}
