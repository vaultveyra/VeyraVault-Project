package com.veyravault.space.ui;

import android.app.AlertDialog;
import android.content.DialogInterface;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.preference.PreferenceManager;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import com.veyravault.space.R;
import com.veyravault.space.core.CloneStore;
import com.veyravault.space.core.LocaleHelper;
import com.veyravault.space.core.ProfileSettings;
import com.veyravault.space.core.ProfileResolver;
import com.veyravault.space.core.ProfileRuntimeApplier;
import com.veyravault.space.core.VirtualHookManager;
import org.osmdroid.config.Configuration;
import org.osmdroid.events.MapEventsReceiver;
import org.osmdroid.tileprovider.tilesource.TileSourceFactory;
import org.osmdroid.util.GeoPoint;
import org.osmdroid.views.MapView;
import org.osmdroid.views.overlay.MapEventsOverlay;
import org.osmdroid.views.overlay.Marker;

public class SetLocationActivity extends BaseActivity {

    private MapView mapView;
    private Marker pinMarker;
    private TextView coordsTv;
    private double selectedLat = 35.6892;
    private double selectedLng = 51.3890;
    private CloneStore.CloneEntry cloneEntry;
    private boolean fa;
    private com.veyravault.space.core.AsyncCloneRepository repository;
    private ProfileSettings cloneProfile;
    private ProfileSettings globalProfile;
    private boolean cloneProfileLoaded;
    private boolean globalProfileLoaded;
    private Button saveButton;
    private TextView resetButton;
    private TextView sourceTv;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        fa = LocaleHelper.isPersian(this);
        Configuration.getInstance().load(getApplicationContext(), PreferenceManager.getDefaultSharedPreferences(getApplicationContext()));
        Configuration.getInstance().setUserAgentValue(getPackageName());

        String pkg = getIntent().getStringExtra("pkg");
        int uid = getIntent().getIntExtra("uid", -1);
        if (pkg == null || pkg.trim().isEmpty() || uid < 0) {
            Toast.makeText(this, fa ? "کلون مقصد معتبر نیست." : "A valid target clone is required.",
                    Toast.LENGTH_LONG).show();
            finish();
            return;
        }
        cloneEntry = CloneStore.getClone(this, pkg, uid);
        if (cloneEntry == null) {
            Toast.makeText(this, fa ? "کلون پیدا نشد یا اطلاعات ذخیره‌شده قابل خواندن نیست." :
                    "Clone not found or stored data is unreadable.", Toast.LENGTH_LONG).show();
            finish();
            return;
        }
        repository = com.veyravault.space.core.AsyncCloneRepository.getInstance(getApplicationContext());

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.WHITE);

        LinearLayout topBar = new LinearLayout(this);
        topBar.setOrientation(LinearLayout.HORIZONTAL);
        topBar.setGravity(Gravity.CENTER_VERTICAL);
        topBar.setPadding(36, 28, 36, 28);

        TextView btnCities = new TextView(this);
        btnCities.setText(fa ? "🌍 انتخاب سریع شهر / مختصات" : "🌍 Quick Cities / Coords");
        btnCities.setTextColor(Color.parseColor("#2563EB"));
        btnCities.setBackgroundResource(R.drawable.bg_pill_lightblue);
        btnCities.setPadding(28, 14, 28, 14);
        btnCities.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) { showCitiesDialog(); }
        });
        topBar.addView(btnCities);

        TextView title = new TextView(this);
        title.setText(getString(R.string.set_location));
        title.setTextSize(19f);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setGravity(Gravity.CENTER);
        topBar.addView(title, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        TextView back = new TextView(this);
        back.setText("›");
        back.setTextSize(28f);
        back.setPadding(20, 0, 20, 0);
        back.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) { finish(); }
        });
        topBar.addView(back);
        root.addView(topBar);

        FrameLayout mapFrame = new FrameLayout(this);
        mapView = new MapView(this);
        mapView.setTileSource(TileSourceFactory.MAPNIK);
        mapView.setMultiTouchControls(true);
        mapView.getController().setZoom(13.5);
        GeoPoint startPoint = new GeoPoint(selectedLat, selectedLng);
        mapView.getController().setCenter(startPoint);

        pinMarker = new Marker(mapView);
        pinMarker.setPosition(startPoint);
        pinMarker.setAnchor(Marker.ANCHOR_CENTER, Marker.ANCHOR_BOTTOM);
        mapView.getOverlays().add(pinMarker);

        MapEventsOverlay eventsOverlay = new MapEventsOverlay(new MapEventsReceiver() {
            @Override
            public boolean singleTapConfirmedHelper(GeoPoint p) {
                updateSelectedPoint(p.getLatitude(), p.getLongitude());
                return true;
            }
            @Override
            public boolean longPressHelper(GeoPoint p) {
                updateSelectedPoint(p.getLatitude(), p.getLongitude());
                return true;
            }
        });
        mapView.getOverlays().add(eventsOverlay);
        mapFrame.addView(mapView);
        root.addView(mapFrame, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));

        LinearLayout bottomCard = new LinearLayout(this);
        bottomCard.setOrientation(LinearLayout.VERTICAL);
        bottomCard.setBackgroundResource(R.drawable.bg_card_rounded);
        bottomCard.setPadding(48, 36, 48, 48);

        TextView locTitle = new TextView(this);
        locTitle.setText(fa ? "موقعیت مکانی (Location)" : "Location");
        locTitle.setTextSize(17f);
        locTitle.setTypeface(Typeface.DEFAULT_BOLD);
        locTitle.setTextColor(Color.parseColor("#111827"));
        bottomCard.addView(locTitle);

        LinearLayout coordBox = new LinearLayout(this);
        coordBox.setOrientation(LinearLayout.VERTICAL);
        coordBox.setBackgroundResource(R.drawable.bg_pill_lightblue);
        coordBox.setPadding(36, 28, 36, 28);
        LinearLayout.LayoutParams cblp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        cblp.setMargins(0, 20, 0, 28);

        coordsTv = new TextView(this);
        coordsTv.setTextSize(19f);
        coordsTv.setTypeface(Typeface.DEFAULT_BOLD);
        coordsTv.setTextColor(Color.parseColor("#111827"));
        coordsTv.setText(String.format("%.4f, %.4f  📍", selectedLat, selectedLng));
        coordBox.addView(coordsTv);

        TextView targetTv = new TextView(this);
        targetTv.setTextSize(13f);
        targetTv.setTextColor(Color.parseColor("#6B7280"));
        targetTv.setText(cloneEntry.displayName + " (Space " + cloneEntry.getSpaceNumber() + ")");
        coordBox.addView(targetTv);
        bottomCard.addView(coordBox, cblp);

        sourceTv = new TextView(this);
        sourceTv.setTextSize(12f);
        sourceTv.setTextColor(Color.parseColor("#6B7280"));
        sourceTv.setPadding(0, 10, 0, 0);
        sourceTv.setText(fa ? "در حال خواندن تنظیمات مؤثر..." : "Loading effective profile...");
        coordBox.addView(sourceTv);

        saveButton = new Button(this);
        saveButton.setBackgroundResource(R.drawable.bg_pill_blue);
        saveButton.setTextColor(Color.WHITE);
        saveButton.setTextSize(15f);
        saveButton.setAllCaps(false);
        saveButton.setText(getString(R.string.set_mock_location));
        saveButton.setEnabled(false);
        saveButton.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) {
                if (cloneProfile == null || globalProfile == null) return;
                saveButton.setEnabled(false);
                resetButton.setEnabled(false);
                ProfileSettings updated = cloneProfile.copy();
                updated.locationEnabled = true;
                updated.latitude = selectedLat;
                updated.longitude = selectedLng;
                repository.saveCloneProfile(cloneEntry.packageName, cloneEntry.userId, updated, result -> {
                    if (isFinishing() || isDestroyed()) return;
                    if (!result.isSuccess()) {
                        saveButton.setEnabled(true);
                        resetButton.setEnabled(true);
                        Toast.makeText(SetLocationActivity.this,
                                (fa ? "ذخیره پروفایل موقعیت ناموفق بود: " : "Location profile save failed: ")
                                        + result.getMessage(), Toast.LENGTH_LONG).show();
                        return;
                    }
                    cloneProfile = updated;
                    syncSavedCloneLocation();
                });
            }
        });
        bottomCard.addView(saveButton);

        resetButton = new TextView(this);
        resetButton.setText(fa ? "بازگشت تنظیمات موقعیت این کلون به پروفایل سراسری" :
                "Reset this clone's location to Global profile");
        resetButton.setTextColor(Color.parseColor("#2563EB"));
        resetButton.setGravity(Gravity.CENTER);
        resetButton.setPadding(0, 24, 0, 0);
        resetButton.setEnabled(false);
        resetButton.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) {
                saveButton.setEnabled(false);
                resetButton.setEnabled(false);
                repository.clearCloneLocationOverrides(cloneEntry.packageName, cloneEntry.userId, result -> {
                    if (isFinishing() || isDestroyed()) return;
                    if (!result.isSuccess()) {
                        saveButton.setEnabled(true);
                        resetButton.setEnabled(true);
                        Toast.makeText(SetLocationActivity.this,
                                (fa ? "بازنشانی به پروفایل سراسری ناموفق بود: " :
                                        "Reset to Global profile failed: ") + result.getMessage(),
                                Toast.LENGTH_LONG).show();
                        return;
                    }
                    if (cloneProfile == null) cloneProfile = new ProfileSettings();
                    cloneProfile.locationEnabled = null;
                    cloneProfile.latitude = null;
                    cloneProfile.longitude = null;
                    VirtualHookManager.LocationApplyResult applied =
                            VirtualHookManager.syncCloneHooks(getApplicationContext(), cloneEntry);
                    showHookResult(applied);
                });
            }
        });
        bottomCard.addView(resetButton);

        root.addView(bottomCard);
        setContentView(root);
        loadLocationProfiles();
    }

    private void loadLocationProfiles() {
        repository.loadCloneProfile(cloneEntry.packageName, cloneEntry.userId, result -> {
            if (isFinishing() || isDestroyed()) return;
            if (!result.isSuccess()) {
                showProfileLoadFailure((fa ? "خواندن تنظیمات کلون ناموفق بود: " :
                        "Could not read clone profile: ") + result.getMessage());
                return;
            }
            cloneProfile = result.getValue();
            cloneProfileLoaded = true;
            applyLoadedProfilesIfReady();
        });
        repository.loadGlobalProfile(result -> {
            if (isFinishing() || isDestroyed()) return;
            if (!result.isSuccess()) {
                showProfileLoadFailure((fa ? "خواندن پروفایل سراسری ناموفق بود: " :
                        "Could not read Global profile: ") + result.getMessage());
                return;
            }
            globalProfile = result.getValue();
            globalProfileLoaded = true;
            applyLoadedProfilesIfReady();
        });
    }

    private void applyLoadedProfilesIfReady() {
        if (!cloneProfileLoaded || !globalProfileLoaded) return;
        ProfileResolver.ResolvedProfile effective = ProfileResolver.resolve(
                cloneProfile, globalProfile, ProfileRuntimeApplier.systemFallback());
        if (effective.latitude != null && effective.longitude != null) {
            updateSelectedPoint(effective.latitude, effective.longitude);
        }
        String state = String.valueOf(effective.locationEnabled) + " (" + effective.locationEnabledSource + ")";
        String coordinates = effective.latitude == null || effective.longitude == null
                ? (fa ? "مختصات مؤثر تنظیم نشده" : "No effective coordinates configured")
                : effective.latitudeSource + " / " + effective.longitudeSource;
        sourceTv.setText(fa ? "وضعیت مؤثر: " + state + "؛ منبع مختصات: " + coordinates
                : "Effective enabled: " + state + "; coordinate source: " + coordinates);
        saveButton.setEnabled(true);
        resetButton.setEnabled(true);
    }

    private void showProfileLoadFailure(String message) {
        saveButton.setEnabled(false);
        resetButton.setEnabled(false);
        Toast.makeText(this, message, Toast.LENGTH_LONG).show();
    }

    private void syncSavedCloneLocation() {
        repository.syncCloneLocationHook(cloneEntry.packageName, cloneEntry.userId, result -> {
            if (isFinishing() || isDestroyed()) return;
            if (!result.isSuccess()) {
                saveButton.setEnabled(true);
                resetButton.setEnabled(true);
                Toast.makeText(this, (fa ? "ذخیره انجام شد اما اجرای همگام‌سازی ناموفق بود: " :
                        "Profile saved, but hook synchronization could not run: ") + result.getMessage(),
                        Toast.LENGTH_LONG).show();
                return;
            }
            showHookResult(result.getValue());
        });
    }

    private void showHookResult(VirtualHookManager.LocationApplyResult result) {
        if (result.status == VirtualHookManager.LocationStatus.APPLIED
                || result.status == VirtualHookManager.LocationStatus.DISABLED) {
            Toast.makeText(this, fa
                    ? "نتیجه موتور تأیید شد: " + result.status + " (" + result.detail + ")"
                    : "Engine result verified: " + result.status + " (" + result.detail + ")",
                    Toast.LENGTH_LONG).show();
            finish();
            return;
        }
        saveButton.setEnabled(true);
        resetButton.setEnabled(true);
        Toast.makeText(this, (fa ? "تنظیم ذخیره شد اما اعمال موقعیت تأیید نشد: " :
                "Profile saved, but engine application was not verified: ")
                + result.status + " (" + result.detail + ")", Toast.LENGTH_LONG).show();
    }

    private void updateSelectedPoint(double lat, double lng) {
        selectedLat = lat;
        selectedLng = lng;
        GeoPoint gp = new GeoPoint(lat, lng);
        pinMarker.setPosition(gp);
        mapView.getController().animateTo(gp);
        mapView.invalidate();
        coordsTv.setText(String.format("%.4f, %.4f  📍", selectedLat, selectedLng));
    }

    private void showCitiesDialog() {
        final String[] names = {
            fa ? "ورود دستی مختصات (Lat, Lng)" : "Manual Coordinates Input",
            "Singapore (1.3588, 103.8742)",
            "New York, USA (40.7128, -74.0060)",
            "London, UK (51.5074, -0.1278)",
            "Frankfurt, Germany (50.1109, 8.6821)",
            "Dubai, UAE (25.2048, 55.2708)",
            "Istanbul, Turkey (41.0082, 28.9784)",
            "Tehran, Iran (35.6892, 51.3890)",
            "Tokyo, Japan (35.6762, 139.6503)"
        };
        final double[][] coords = {
            {0, 0},
            {1.3588, 103.8742},
            {40.7128, -74.0060},
            {51.5074, -0.1278},
            {50.1109, 8.6821},
            {25.2048, 55.2708},
            {41.0082, 28.9784},
            {35.6892, 51.3890},
            {35.6762, 139.6503}
        };
        new AlertDialog.Builder(this)
                .setTitle(fa ? "انتخاب شهر یا مختصات" : "Select City or Coordinates")
                .setItems(names, new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface d, int which) {
                        if (which == 0) {
                            final EditText et = new EditText(SetLocationActivity.this);
                            et.setHint("e.g. 1.3588, 103.8742");
                            new AlertDialog.Builder(SetLocationActivity.this)
                                    .setTitle("Latitude, Longitude")
                                    .setView(et)
                                    .setPositiveButton("OK", new DialogInterface.OnClickListener() {
                                        @Override
                                        public void onClick(DialogInterface d2, int w2) {
                                            try {
                                                String[] p = et.getText().toString().split(",");
                                                updateSelectedPoint(Double.parseDouble(p[0].trim()), Double.parseDouble(p[1].trim()));
                                            } catch (Exception ignored) {}
                                        }
                                    }).show();
                        } else {
                            updateSelectedPoint(coords[which][0], coords[which][1]);
                        }
                    }
                }).show();
    }
}
