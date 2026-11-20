package com.veyravault.space.ui;

import android.content.Intent;
import android.content.Context;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.net.NetworkInfo;
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
import com.veyravault.space.core.ProfileSettings;
import com.veyravault.space.core.ProfileResolver;
import com.veyravault.space.core.ProfileRuntimeApplier;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.TimeZone;

public class DashboardActivity extends BaseActivity {
    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        final boolean fa = LocaleHelper.isPersian(this);
        ScrollView scroll = new ScrollView(this);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(24),dp(28),dp(24),dp(32));
        root.setBackgroundColor(Color.rgb(243,245,249));
        scroll.addView(root);
        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setGravity(android.view.Gravity.CENTER_VERTICAL);
        TextView title = new TextView(this);
        title.setText("VeyraVault");
        title.setTextSize(26);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setTextColor(UiPalette.textPrimary(this));
        header.addView(title, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        header.addView(createImmediateLockAction(fa));
        root.addView(header);
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

        final TextView networkSummary = addSummaryCard(root,
                fa ? "شبکه میزبان" : "Host Network",
                fa ? "در حال بررسی وضعیت اتصال…" : "Checking connectivity…");
        final TextView profileSummary = addSummaryCard(root,
                fa ? "محیط مؤثر آخرین Clone" : "Effective Environment — Last Clone",
                fa ? "در حال خواندن پروفایل‌ها…" : "Reading environment profiles…");
        final TextView globalMetadataSummary = addSummaryCard(root,
                fa ? "مشخصات سراسری ذخیره‌شده (فقط Metadata)" : "Saved Global Device Metadata",
                fa ? "در حال خواندن اطلاعات…" : "Reading saved metadata…");
        addSummaryCard(root,
                fa ? "IP عمومی" : "Public IP",
                fa ? "بررسی نشده است؛ داشبورد هیچ درخواست جست‌وجوی IP به سرویس خارجی ارسال نکرده است."
                   : "Not checked. The Dashboard has not sent a public-IP lookup request to an external service.");

        networkSummary.setText(describeHostNetwork(fa));
        loadGlobalDeviceMetadata(globalMetadataSummary, fa);

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
                            profileSummary.setText(fa
                                    ? "پروفایل مؤثر در دسترس نیست؛ فهرست Clone قابل اعتبارسنجی نبود."
                                    : "Effective profile unavailable because the Clone registry could not be validated.");
                            return;
                        }
                        Set<Integer> spaces = new HashSet<Integer>();
                        for (CloneStore.CloneEntry clone : result.getValue()) spaces.add(clone.getSpaceNumber());
                        cloneCount.setText(String.valueOf(result.getValue().size()));
                        spaceCount.setText(String.valueOf(spaces.size()));
                        loadEffectiveProfileSummary(result.getValue(), profileSummary, fa);
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

    private TextView addSummaryCard(LinearLayout root, String heading, String initialValue) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(16), dp(14), dp(16), dp(14));
        card.setBackgroundResource(com.veyravault.space.R.drawable.bg_card_rounded);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        params.topMargin = dp(10);

        TextView title = new TextView(this);
        title.setText(heading);
        title.setTextSize(14f);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setTextColor(Color.rgb(31, 41, 55));
        card.addView(title);

        TextView value = new TextView(this);
        value.setText(initialValue);
        value.setTextSize(12f);
        value.setTextColor(Color.rgb(75, 85, 99));
        value.setPadding(0, dp(6), 0, 0);
        card.addView(value);

        root.addView(card, params);
        return value;
    }

    private String describeHostNetwork(boolean fa) {
        ConnectivityManager manager =
                (ConnectivityManager) getSystemService(Context.CONNECTIVITY_SERVICE);
        if (manager == null) {
            return fa ? "وضعیت شبکه میزبان در دسترس نیست."
                    : "Host network status is unavailable.";
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            Network active = manager.getActiveNetwork();
            NetworkCapabilities capabilities = active == null
                    ? null : manager.getNetworkCapabilities(active);
            if (capabilities == null) {
                return fa ? "شبکه میزبان متصل نیست یا وضعیت آن قابل خواندن نیست."
                        : "Host network is offline or its state is unavailable.";
            }

            String transport;
            if (capabilities.hasTransport(NetworkCapabilities.TRANSPORT_VPN)) {
                transport = fa ? "حمل‌ونقل VPN سیستم" : "System VPN transport";
            } else if (capabilities.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)) {
                transport = "Wi-Fi";
            } else if (capabilities.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR)) {
                transport = fa ? "شبکه موبایل" : "Cellular";
            } else if (capabilities.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET)) {
                transport = "Ethernet";
            } else {
                transport = fa ? "شبکه دیگر" : "Other network";
            }

            boolean internetCapability =
                    capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET);
            boolean validated =
                    capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED);
            String status = validated
                    ? (fa ? "اینترنت توسط Android تأیید شده" : "Android reports Internet validated")
                    : internetCapability
                        ? (fa ? "شبکه دارای قابلیت Internet است؛ اعتبارسنجی نشده"
                              : "Internet capability present; not validated")
                        : (fa ? "اتصال شبکه بدون قابلیت Internet" : "Connected without Internet capability");
            return (fa ? "شبکه میزبان: " : "Host network: ") + transport + " — " + status
                    + (capabilities.hasTransport(NetworkCapabilities.TRANSPORT_VPN)
                        ? (fa ? ". این وضعیت به‌تنهایی مسیر هر Clone را اثبات نمی‌کند."
                              : ". This alone does not prove each Clone traffic route.")
                        : "");
        }

        @SuppressWarnings("deprecation")
        NetworkInfo info = manager.getActiveNetworkInfo();
        if (info == null || !info.isConnected()) {
            return fa ? "شبکه میزبان متصل نیست." : "Host network is offline.";
        }
        @SuppressWarnings("deprecation")
        String typeName = info.getTypeName();
        return (fa ? "شبکه میزبان: " : "Host network: ") + typeName
                + (fa ? " (متصل؛ دسترسی اینترنت جداگانه تأیید نشده است)"
                      : " (connected; Internet reachability is not independently verified)");
    }

    private void loadGlobalDeviceMetadata(TextView target, boolean fa) {
        AsyncCloneRepository.getInstance(getApplicationContext()).loadGlobalEnvironment(result -> {
            if (isFinishing() || isDestroyed()) return;
            if (!result.isSuccess() || result.getValue() == null) {
                target.setText((fa ? "خواندن Metadata سراسری ناموفق بود: "
                        : "Could not read Global metadata: ") + result.getMessage());
                return;
            }
            CloneStore.GlobalEnvConfig config = result.getValue();
            String brand = safeDisplayValue(config.brand);
            String model = safeDisplayValue(config.model);
            String country = safeDisplayValue(config.countryIso);
            String operator = safeDisplayValue(config.simOperator);
            target.setText((fa ? "برند/مدل ذخیره‌شده: " : "Saved brand/model: ")
                    + brand + " / " + model
                    + (fa ? "\nکد کشور ذخیره‌شده: " : "\nSaved country code: ") + country
                    + (fa ? "\nکد اپراتور ذخیره‌شده: " : "\nSaved operator code: ") + operator
                    + (fa ? "\nاین مقادیر فقط Metadata هستند و موتور فعلی آن‌ها را به برنامه‌های Clone اعمال نمی‌کند."
                          : "\nThese are metadata only; the pinned engine does not apply them to cloned apps."));
        });
    }

    private void loadEffectiveProfileSummary(List<CloneStore.CloneEntry> clones,
                                             TextView target, boolean fa) {
        AsyncCloneRepository repository = AsyncCloneRepository.getInstance(getApplicationContext());
        repository.loadGlobalProfile(globalResult -> {
            if (isFinishing() || isDestroyed()) return;
            if (!globalResult.isSuccess() || globalResult.getValue() == null) {
                target.setText((fa ? "خواندن پیش‌فرض‌های سراسری ناموفق بود: "
                        : "Could not read Global defaults: ") + globalResult.getMessage());
                return;
            }
            ProfileSettings global = globalResult.getValue();
            repository.loadLastActiveLaunch(activeResult -> {
                if (isFinishing() || isDestroyed()) return;
                if (!activeResult.isSuccess()) {
                    target.setText((fa ? "خواندن آخرین Clone ناموفق بود: "
                            : "Could not read the last launched Clone: ") + activeResult.getMessage());
                    return;
                }
                CloneStore.CloneEntry active = activeResult.getValue();
                if (active == null) {
                    renderEffectiveProfile(target, new ProfileSettings(), global, fa,
                            fa ? "آخرین Clone ثبت‌شده‌ای وجود ندارد؛ پیش‌فرض Global/System نمایش داده می‌شود."
                               : "No last-launched Clone is recorded; showing Global/System defaults.");
                    return;
                }

                boolean identityFound = false;
                for (CloneStore.CloneEntry entry : clones) {
                    if (entry != null && active.packageName != null
                            && active.packageName.equals(entry.packageName)
                            && active.userId == entry.userId) {
                        identityFound = true;
                        break;
                    }
                }
                if (!identityFound) {
                    target.setText(fa
                            ? "آخرین نشانگر اجرا با Registry فعلی Clone تطبیق ندارد؛ پروفایل Clone نمایش داده نمی‌شود."
                            : "The last-launch marker does not match the current Clone registry; Clone profile is not displayed.");
                    return;
                }

                repository.loadCloneProfile(active.packageName, active.userId, cloneResult -> {
                    if (isFinishing() || isDestroyed()) return;
                    if (!cloneResult.isSuccess() || cloneResult.getValue() == null) {
                        target.setText((fa ? "خواندن پروفایل Clone ناموفق بود: "
                                : "Could not read Clone profile: ") + cloneResult.getMessage());
                        return;
                    }
                    String label = active.displayName == null || active.displayName.trim().isEmpty()
                            ? active.packageName : active.displayName;
                    String context = (fa ? "آخرین Clone ثبت‌شده: " : "Last recorded Clone: ")
                            + label + " (" + (fa ? "فضای " : "Space ") + active.getSpaceNumber() + ")";
                    renderEffectiveProfile(target, cloneResult.getValue(), global, fa, context);
                });
            });
        });
    }

    private void renderEffectiveProfile(TextView target, ProfileSettings clone,
                                        ProfileSettings global, boolean fa, String context) {
        ProfileResolver.ResolvedProfile effective = ProfileResolver.resolve(
                clone, global, ProfileRuntimeApplier.systemFallback());
        String locale = effective.localeTag == null ? "UNSET"
                : effective.localeTag + " (" + effective.localeSource + ")";
        String zone = effective.timeZoneId == null ? "UNSET"
                : effective.timeZoneId + " (" + effective.timeZoneSource + ")";
        String location = effective.locationEnabled == null ? "UNSET"
                : (Boolean.TRUE.equals(effective.locationEnabled)
                    ? (fa ? "فعال" : "Enabled") : (fa ? "غیرفعال" : "Disabled"))
                    + " (" + effective.locationEnabledSource + ")";
        target.setText(context
                + (fa ? "\nزبان مؤثر: " : "\nEffective Locale: ") + locale
                + (fa ? "\nمنطقه زمانی مؤثر: " : "\nEffective Time Zone: ") + zone
                + (fa ? "\nوضعیت موقعیت مؤثر: " : "\nEffective location policy: ") + location
                + (fa ? "\nمنبع هر فیلد جداگانه محاسبه می‌شود: Clone ← Global ← System."
                      : "\nEach field resolves independently: Clone → Global → System."));
    }

    private String safeDisplayValue(String value) {
        return value == null || value.trim().isEmpty() ? "—" : value.trim();
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