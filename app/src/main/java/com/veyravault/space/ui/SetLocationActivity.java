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

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        fa = LocaleHelper.isPersian(this);
        Configuration.getInstance().load(getApplicationContext(), PreferenceManager.getDefaultSharedPreferences(getApplicationContext()));
        Configuration.getInstance().setUserAgentValue(getPackageName());

        String pkg = getIntent().getStringExtra("pkg");
        int uid = getIntent().getIntExtra("uid", 0);
        cloneEntry = CloneStore.getClone(this, pkg, uid);
        if (cloneEntry != null && (cloneEntry.latitude != 0 || cloneEntry.longitude != 0)) {
            selectedLat = cloneEntry.latitude;
            selectedLng = cloneEntry.longitude;
        }

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
        targetTv.setText(cloneEntry != null
                ? (cloneEntry.displayName + " (Space " + cloneEntry.getSpaceNumber() + ")")
                : "Global Mock GPS");
        coordBox.addView(targetTv);
        bottomCard.addView(coordBox, cblp);

        Button btnSave = new Button(this);
        btnSave.setBackgroundResource(R.drawable.bg_pill_blue);
        btnSave.setTextColor(Color.WHITE);
        btnSave.setTextSize(15f);
        btnSave.setAllCaps(false);
        btnSave.setText(getString(R.string.set_mock_location));
        btnSave.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                if (cloneEntry != null) {
                    cloneEntry.mockGpsEnabled = true;
                    cloneEntry.latitude = selectedLat;
                    cloneEntry.longitude = selectedLng;
                    CloneStore.upsertClone(SetLocationActivity.this, cloneEntry);
                    VirtualHookManager.syncCloneHooks(SetLocationActivity.this, cloneEntry);
                }
                Toast.makeText(SetLocationActivity.this,
                        fa ? "موقعیت مکانی مجازی ثبت و فعال شد!" : "Mock location set and activated!",
                        Toast.LENGTH_SHORT).show();
                finish();
            }
        });
        bottomCard.addView(btnSave);

        TextView btnReset = new TextView(this);
        btnReset.setText(fa ? "غیرفعال کردن موقعیت مجازی برای این برنامه" : "Disable mock location for this clone");
        btnReset.setTextColor(Color.parseColor("#EF4444"));
        btnReset.setGravity(Gravity.CENTER);
        btnReset.setPadding(0, 24, 0, 0);
        btnReset.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                if (cloneEntry != null) {
                    cloneEntry.mockGpsEnabled = false;
                    CloneStore.upsertClone(SetLocationActivity.this, cloneEntry);
                    VirtualHookManager.syncCloneHooks(SetLocationActivity.this, cloneEntry);
                }
                finish();
            }
        });
        bottomCard.addView(btnReset);

        root.addView(bottomCard);
        setContentView(root);
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
