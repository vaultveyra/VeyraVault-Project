package com.veyravault.space.ui;

import android.graphics.Typeface;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.View;
import android.view.ViewGroup;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.RadioButton;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import com.veyravault.space.R;
import com.veyravault.space.core.LocaleHelper;
import com.veyravault.space.security.AppDisguiseManager;

import java.util.Locale;

public class AppIconNameActivity extends BaseActivity {
    private static final int[] ICONS = {
            R.drawable.ic_launcher_vault,
            R.drawable.ic_disguise_calc,
            R.drawable.ic_disguise_calendar,
            R.drawable.ic_disguise_notes,
            R.drawable.ic_disguise_weather
    };

    private static final String[] ENGLISH_LABELS = {
            "VeyraVault", "Calculator", "Calendar", "Notes", "Weather"
    };

    private static final String[] PERSIAN_LABELS = {
            "VeyraVault", "ماشین‌حساب", "تقویم", "یادداشت‌ها", "آب‌وهوا"
    };

    private LinearLayout optionsContainer;
    private EditText searchInput;
    private boolean fa;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        fa = LocaleHelper.isPersian(this);

        ScrollView scroll = new ScrollView(this);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(22), dp(22), dp(22), dp(30));
        root.setBackgroundColor(UiPalette.page(this));
        scroll.addView(root);

        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setGravity(android.view.Gravity.CENTER_VERTICAL);
        TextView title = new TextView(this);
        title.setText(fa ? "آیکون و نام لانچر" : "Launcher Icon & Label");
        title.setTextSize(21f);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setTextColor(UiPalette.textPrimary(this));
        header.addView(title, new LinearLayout.LayoutParams(
                0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        header.addView(createImmediateLockAction(fa));
        root.addView(header);

        TextView explanation = new TextView(this);
        explanation.setText(fa
                ? "یکی از پنج آیکون و نامی را انتخاب کنید که واقعاً در Manifest برنامه تعریف شده است. این تغییر فقط ظاهر میانبر لانچر را عوض می‌کند و قابلیت امنیتی یا مخفی‌سازی نیست."
                : "Choose one of the five icon and label pairs actually declared in this app's manifest. This changes the launcher entry only; it is not a security or concealment feature.");
        explanation.setTextSize(13f);
        explanation.setTextColor(UiPalette.textSecondary(this));
        explanation.setPadding(0, dp(10), 0, dp(16));
        root.addView(explanation);

        searchInput = new EditText(this);
        searchInput.setSingleLine(true);
        searchInput.setTextSize(14f);
        searchInput.setHint(fa ? "جستجوی گزینه‌های موجود…" : "Search available options…");
        searchInput.setHintTextColor(UiPalette.muted(this));
        searchInput.setTextColor(UiPalette.textPrimary(this));
        searchInput.setPadding(dp(14), dp(10), dp(14), dp(10));
        searchInput.setBackgroundResource(R.drawable.bg_card_rounded);
        root.addView(searchInput, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        optionsContainer = new LinearLayout(this);
        optionsContainer.setOrientation(LinearLayout.VERTICAL);
        root.addView(optionsContainer);

        searchInput.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence text, int start, int count, int after) { }
            @Override public void onTextChanged(CharSequence text, int start, int before, int count) {
                renderOptions(text == null ? "" : text.toString());
            }
            @Override public void afterTextChanged(Editable editable) { }
        });

        renderOptions("");
        setContentView(scroll);
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (optionsContainer != null) {
            String query = searchInput == null ? "" : searchInput.getText().toString();
            renderOptions(query);
        }
    }

    private void renderOptions(String query) {
        if (optionsContainer == null) return;
        optionsContainer.removeAllViews();
        String normalized = query == null ? "" : query.trim().toLowerCase(Locale.ROOT);
        int activeIndex = AppDisguiseManager.getActiveDisguiseIndex(this);

        for (int i = 0; i < ICONS.length; i++) {
            final int index = i;
            final String label = fa ? PERSIAN_LABELS[i] : ENGLISH_LABELS[i];
            String searchable = (ENGLISH_LABELS[i] + " " + PERSIAN_LABELS[i])
                    .toLowerCase(Locale.ROOT);
            if (!normalized.isEmpty() && !searchable.contains(normalized)) continue;

            LinearLayout card = new LinearLayout(this);
            card.setOrientation(LinearLayout.HORIZONTAL);
            card.setGravity(android.view.Gravity.CENTER_VERTICAL);
            card.setPadding(dp(14), dp(12), dp(14), dp(12));
            card.setBackgroundResource(R.drawable.bg_card_rounded);
            LinearLayout.LayoutParams cardParams = new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
            cardParams.topMargin = dp(10);

            ImageView icon = new ImageView(this);
            icon.setImageResource(ICONS[i]);
            icon.setContentDescription(label);
            icon.setScaleType(ImageView.ScaleType.FIT_CENTER);
            card.addView(icon, new LinearLayout.LayoutParams(dp(52), dp(52)));

            LinearLayout labels = new LinearLayout(this);
            labels.setOrientation(LinearLayout.VERTICAL);
            labels.setPadding(dp(14), 0, dp(8), 0);
            labels.setGravity(android.view.Gravity.CENTER_VERTICAL);
            labels.addView(createOptionTitle(label));
            TextView note = new TextView(this);
            note.setText(i == activeIndex
                    ? (fa ? "انتخاب‌شده" : "Currently selected")
                    : (fa ? "گزینهٔ آمادهٔ لانچر" : "Bundled launcher option"));
            note.setTextSize(11f);
            note.setTextColor(i == activeIndex
                    ? UiPalette.success(this) : UiPalette.muted(this));
            labels.addView(note);
            card.addView(labels, new LinearLayout.LayoutParams(
                    0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

            RadioButton selected = new RadioButton(this);
            selected.setClickable(false);
            selected.setFocusable(false);
            selected.setChecked(i == activeIndex);
            selected.setContentDescription(fa ? "گزینهٔ انتخاب‌شده" : "Selected launcher option");
            card.addView(selected);

            View.OnClickListener choose = view -> {
                boolean applied = AppDisguiseManager.applyDisguise(AppIconNameActivity.this, index);
                if (applied) {
                    Toast.makeText(AppIconNameActivity.this,
                            (fa ? "آیکون و نام لانچر به‌روزرسانی شد: " : "Launcher icon and label updated: ")
                                    + label
                                    + (fa ? "؛ ممکن است لانچر کمی زمان برای تازه‌سازی نیاز داشته باشد."
                                          : ". The launcher may take a moment to refresh."),
                            Toast.LENGTH_LONG).show();
                    renderOptions(searchInput == null ? "" : searchInput.getText().toString());
                } else {
                    Toast.makeText(AppIconNameActivity.this,
                            fa ? "تغییر آیکون تأیید نشد؛ وضعیت قبلی را بررسی کنید."
                               : "The launcher change could not be verified. Check the current selection.",
                            Toast.LENGTH_LONG).show();
                }
            };
            card.setOnClickListener(choose);
            selected.setOnClickListener(choose);
            optionsContainer.addView(card, cardParams);
        }

        if (optionsContainer.getChildCount() == 0) {
            TextView empty = new TextView(this);
            empty.setText(fa ? "گزینه‌ای با این جستجو پیدا نشد." : "No available launcher option matches this search.");
            empty.setTextColor(UiPalette.textSecondary(this));
            empty.setPadding(0, dp(18), 0, dp(12));
            optionsContainer.addView(empty);
        }
    }

    private TextView createOptionTitle(String label) {
        TextView title = new TextView(this);
        title.setText(label);
        title.setTextSize(15f);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setTextColor(UiPalette.textPrimary(this));
        return title;
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

}
