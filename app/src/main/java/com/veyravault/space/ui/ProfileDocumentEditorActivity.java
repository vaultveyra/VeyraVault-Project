package com.veyravault.space.ui;

import android.os.Bundle;
import android.text.InputType;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import com.veyravault.space.core.AsyncCloneRepository;
import com.veyravault.space.core.CloneStore;
import com.veyravault.space.core.LocaleHelper;
import com.veyravault.space.core.ProfileDocument;
import com.veyravault.space.core.ProfileDocumentResolver;
import com.veyravault.space.core.ProfileFieldRegistry;
import com.veyravault.space.core.ProfileRuntimeStatusStore;

import java.text.DateFormat;
import java.util.Date;
import java.util.LinkedHashMap;
import java.util.Map;

/** Registry-driven Global / per-Clone profile editor with asynchronous, field-scoped writes. */
public final class ProfileDocumentEditorActivity extends BaseActivity {
    private interface Mutation {
        void run(AsyncCloneRepository.Callback<Boolean> callback);
    }

    private AsyncCloneRepository repository;
    private boolean fa;
    private boolean cloneMode;
    private String packageName;
    private int userId;
    private boolean cloneLoaded;
    private boolean globalLoaded;
    private boolean registryLoaded;
    private boolean runtimeStatusLoaded;
    private boolean runtimeStatusUnavailable;
    private boolean loadFailed;
    private ProfileRuntimeStatusStore.Snapshot runtimeStatus;
    private ProfileDocument cloneDocument;
    private ProfileDocument globalDocument;
    private LinearLayout root;

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        fa = LocaleHelper.isPersian(this);
        packageName = getIntent().getStringExtra("pkg");
        userId = getIntent().getIntExtra("uid", -1);
        boolean forceGlobal = getIntent().getBooleanExtra("mode_global", false);
        cloneMode = !forceGlobal && packageName != null && !packageName.trim().isEmpty() && userId >= 0;
        if (!forceGlobal && packageName != null && !cloneMode) {
            Toast.makeText(this, fa ? "شناسه کلون معتبر نیست." : "Clone identity is invalid.",
                    Toast.LENGTH_LONG).show();
            finish();
            return;
        }
        repository = AsyncCloneRepository.getInstance(getApplicationContext());
        showLoading();
        loadDocuments();
    }

    private void showLoading() {
        ScrollView scroll = new ScrollView(this);
        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(20), dp(24), dp(20), dp(40));
        root.setBackgroundColor(UiPalette.page(this));
        root.addView(title());
        TextView loading = new TextView(this);
        loading.setText(fa ? "در حال خواندن و اعتبارسنجی تنظیمات…" : "Loading and validating profile fields…");
        loading.setTextColor(UiPalette.textSecondary(this));
        loading.setPadding(0, dp(16), 0, dp(16));
        root.addView(loading);
        scroll.addView(root);
        setContentView(scroll);
    }

    private TextView title() {
        TextView title = new TextView(this);
        title.setText(cloneMode
                ? (fa ? "پروفایل کامل محیط کلون" : "Complete Clone Environment Profile")
                : (fa ? "پروفایل کامل سراسری" : "Complete Global Environment Profile"));
        title.setTextSize(22f);
        title.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
        title.setTextColor(UiPalette.textPrimary(this));
        return title;
    }

    private void loadDocuments() {
        cloneLoaded = !cloneMode;
        globalLoaded = false;
        registryLoaded = !cloneMode;
        runtimeStatusLoaded = !cloneMode;
        runtimeStatusUnavailable = false;
        runtimeStatus = null;
        loadFailed = false;
        if (cloneMode) {
            repository.loadClones(result -> {
                if (isFinishing() || isDestroyed()) return;
                if (!result.isSuccess() || result.getValue() == null) {
                    failLoad((fa ? "خواندن فهرست کلون‌ها ناموفق بود: " :
                            "Could not read Clone registry: ") + result.getMessage());
                    return;
                }
                boolean found = false;
                for (CloneStore.CloneEntry entry : result.getValue()) {
                    if (entry != null && packageName.equals(entry.packageName) && userId == entry.userId) {
                        found = true;
                        break;
                    }
                }
                if (!found) {
                    failLoad(fa ? "کلون در فهرست معتبر پیدا نشد." :
                            "The requested Clone is not in the validated registry.");
                    return;
                }
                registryLoaded = true;
                finishLoadIfReady();
            });
            repository.loadCloneProfileDocument(packageName, userId, result -> {
                if (isFinishing() || isDestroyed()) return;
                if (!result.isSuccess() || result.getValue() == null) {
                    failLoad((fa ? "خواندن سند کلون ناموفق بود: " :
                            "Could not read Clone profile document: ") + result.getMessage());
                    return;
                }
                cloneDocument = result.getValue();
                cloneLoaded = true;
                finishLoadIfReady();
            });
            repository.loadCloneRuntimeStatus(packageName, userId, result -> {
                if (isFinishing() || isDestroyed()) return;
                if (!result.isSuccess() || result.getValue() == null) {
                    runtimeStatusUnavailable = true;
                } else {
                    runtimeStatus = result.getValue();
                }
                runtimeStatusLoaded = true;
                finishLoadIfReady();
            });
        } else {
            cloneDocument = new ProfileDocument();
        }
        repository.loadGlobalProfileDocument(result -> {
            if (isFinishing() || isDestroyed()) return;
            if (!result.isSuccess() || result.getValue() == null) {
                failLoad((fa ? "خواندن سند سراسری ناموفق بود: " :
                        "Could not read Global profile document: ") + result.getMessage());
                return;
            }
            globalDocument = result.getValue();
            globalLoaded = true;
            finishLoadIfReady();
        });
    }

    private void finishLoadIfReady() {
        if (loadFailed || !cloneLoaded || !globalLoaded || !registryLoaded || !runtimeStatusLoaded) return;
        buildEditor();
    }

    private void buildEditor() {
        ScrollView scroll = new ScrollView(this);
        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(20), dp(24), dp(20), dp(40));
        root.setBackgroundColor(UiPalette.page(this));
        root.addView(title());

        TextView identity = new TextView(this);
        identity.setText(cloneMode ? packageName + "  ·  user " + userId
                : (fa ? "پیش‌فرض عمومی برای کلون‌های بدون Override معتبر" :
                        "Global fallback for Clones without a valid per-field override"));
        identity.setTextSize(12f);
        identity.setTextColor(UiPalette.textSecondary(this));
        identity.setPadding(0, dp(8), 0, dp(10));
        root.addView(identity);

        TextView explanation = new TextView(this);
        explanation.setText(fa
                ? "اولویت هر فیلد: Override کلون ← Global ← Safe Isolated Default. ذخیره‌شدن به معنی اعمال‌شدن نیست؛ فقط Adapter و Readback واقعی وضعیت را تأیید می‌کنند. فیلدهای مشاهده‌ای و محدودشده قابل ویرایش نیستند."
                : "Per-field priority: Clone override → Global → Safe Isolated Default. Stored does not mean applied; only a real adapter and readback can verify application. Observed-only and restricted fields are read-only.");
        explanation.setTextSize(12f);
        explanation.setTextColor(UiPalette.textSecondary(this));
        explanation.setPadding(0, 0, 0, dp(16));
        root.addView(explanation);
        if (cloneMode) root.addView(runtimeStatusSummary());

        Map<String, ProfileDocumentResolver.FieldResult> resolved =
                ProfileDocumentResolver.resolveAll(cloneDocument, globalDocument);
        Map<String, ProfileFieldRegistry.ApplyStatus> displayStatuses = displayStatuses(resolved);
        addSummary(resolved, displayStatuses);
        String lastCategory = null;
        for (ProfileFieldRegistry.Field field : ProfileFieldRegistry.all()) {
            if (!field.category.equals(lastCategory)) {
                lastCategory = field.category;
                TextView category = new TextView(this);
                category.setText(displayCategory(field.category));
                category.setTextSize(17f);
                category.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
                category.setTextColor(UiPalette.textPrimary(this));
                category.setPadding(0, dp(22), 0, dp(10));
                root.addView(category);
            }
            root.addView(buildFieldCard(field, resolved.get(field.key), displayStatuses.get(field.key)));
        }
        scroll.addView(root);
        setContentView(scroll);
    }

    private Map<String, ProfileFieldRegistry.ApplyStatus> displayStatuses(
            Map<String, ProfileDocumentResolver.FieldResult> resolved) {
        Map<String, ProfileFieldRegistry.ApplyStatus> statuses = new LinkedHashMap<>();
        for (ProfileDocumentResolver.FieldResult field : resolved.values()) {
            ProfileFieldRegistry.ApplyStatus status = field.status;
            if (cloneMode && runtimeStatus != null && runtimeStatus.current) {
                ProfileFieldRegistry.ApplyStatus verified = runtimeStatus.statuses.get(field.key);
                if (verified != null) status = verified;
            }
            statuses.put(field.key, status);
        }
        return statuses;
    }

    private TextView runtimeStatusSummary() {
        TextView info = new TextView(this);
        info.setTextSize(11f);
        info.setTextColor(UiPalette.textSecondary(this));
        info.setPadding(dp(12), dp(10), dp(12), dp(10));
        info.setBackgroundResource(com.veyravault.space.R.drawable.bg_card_rounded);

        String message;
        if (runtimeStatusUnavailable) {
            message = fa
                    ? "وضعیت Readback در دسترس نیست؛ هیچ فیلدی به‌عنوان اعمال‌شده نمایش داده نمی‌شود."
                    : "Runtime readback status is unavailable; no field is presented as applied.";
        } else if (runtimeStatus == null || !runtimeStatus.exists) {
            message = fa
                    ? "هنوز Readback معتبر برای این کلون ثبت نشده است. پس از اجرای کلون و تأیید واقعی Locale/Time Zone وضعیت ثبت می‌شود."
                    : "No runtime readback has been recorded for this Clone yet. A result is stored only after the Clone runs and Locale/Time Zone are read back.";
        } else if (!runtimeStatus.current) {
            message = fa
                    ? "Readback قبلی با پروفایل مؤثر فعلی تطابق ندارد؛ وضعیت فیلدهای Runtime اکنون NOT_TESTED است."
                    : "The previous readback no longer matches the effective profile; Runtime fields are now NOT_TESTED.";
        } else {
            String when = DateFormat.getDateTimeInstance(
                    DateFormat.SHORT, DateFormat.MEDIUM).format(new Date(runtimeStatus.updatedAt));
            message = (fa ? "آخرین Readback تأییدشده: " : "Last verified readback: ")
                    + when + " · " + (fa ? "پردازه: " : "Process: ") + runtimeStatus.processName
                    + (fa ? " · این سابقه، زنده‌بودن فعلی پردازه را ثابت نمی‌کند."
                            : " · This is historical evidence, not proof that the process is still alive.");
        }
        info.setText(message);
        return info;
    }

    private void addSummary(Map<String, ProfileDocumentResolver.FieldResult> resolved,
                            Map<String, ProfileFieldRegistry.ApplyStatus> displayStatuses) {
        int applied = 0, stored = 0, unsupported = 0, notTested = 0, failed = 0, notApplicable = 0;
        for (ProfileDocumentResolver.FieldResult field : resolved.values()) {
            switch (displayStatuses.get(field.key)) {
                case APPLIED: applied++; break;
                case STORED_ONLY: stored++; break;
                case UNSUPPORTED: unsupported++; break;
                case NOT_APPLICABLE: notApplicable++; break;
                case NOT_TESTED: notTested++; break;
                case FAILED: failed++; break;
                default: break;
            }
        }
        TextView summary = new TextView(this);
        summary.setText("Fields: " + resolved.size()
                + "  ·  Applied: " + applied
                + "  ·  Stored only: " + stored
                + "  ·  Unsupported: " + unsupported
                + "  ·  Not tested: " + notTested
                + "  ·  Failed: " + failed
                + "  ·  Not applicable: " + notApplicable);
        summary.setTextSize(12f);
        summary.setTextColor(UiPalette.textPrimary(this));
        summary.setPadding(dp(12), dp(12), dp(12), dp(12));
        summary.setBackgroundResource(com.veyravault.space.R.drawable.bg_card_rounded);
        root.addView(summary);
    }

    private View buildFieldCard(ProfileFieldRegistry.Field field,
                                ProfileDocumentResolver.FieldResult effective,
                                ProfileFieldRegistry.ApplyStatus displayStatus) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(14), dp(14), dp(14), dp(14));
        card.setBackgroundResource(com.veyravault.space.R.drawable.bg_card_rounded);
        LinearLayout.LayoutParams cardParams = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        cardParams.bottomMargin = dp(10);
        card.setLayoutParams(cardParams);

        ProfileDocument current = cloneMode ? cloneDocument : globalDocument;
        Object storedValue = current == null ? null : current.get(field.key);
        ProfileDocument.FieldState state = current == null ? null : current.state(field.key);

        TextView heading = new TextView(this);
        heading.setText(field.label + "  ·  " + field.key);
        heading.setTextSize(15f);
        heading.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
        heading.setTextColor(UiPalette.textPrimary(this));
        card.addView(heading);

        TextView effectiveText = new TextView(this);
        effectiveText.setText((fa ? "مقدار مؤثر: " : "Effective: ")
                + valueText(effective.value) + "  |  Source: " + effective.source
                + "  |  " + (cloneMode && field.capability == ProfileFieldRegistry.Capability.PROCESS_SCOPED
                        ? "Last readback: " : "Status: ") + displayStatus);
        effectiveText.setTextSize(12f);
        effectiveText.setTextColor(UiPalette.textSecondary(this));
        effectiveText.setPadding(0, dp(7), 0, dp(7));
        card.addView(effectiveText);

        TextView capability = new TextView(this);
        capability.setText(field.capability.name() + "  ·  " + field.validationRule);
        capability.setTextSize(11f);
        capability.setTextColor(UiPalette.textSecondary(this));
        card.addView(capability);

        // Expose the full reviewed capability boundary to the user. These are
        // declarative support/readback metadata, not a claim that the field is applied.
        TextView technical = new TextView(this);
        technical.setText((fa ? "آداپتور: " : "Adapter: ") + field.adapterId
                + "\n" + (fa ? "پشتیبانی API: " : "API support: ") + field.apiSupport
                + "\n" + (fa ? "کلاس حریم خصوصی: " : "Privacy class: ") + field.privacyClass
                + "\n" + (fa ? "روش Readback: " : "Readback method: ") + field.readbackMethod);
        technical.setTextSize(10.5f);
        technical.setTextColor(UiPalette.textSecondary(this));
        technical.setPadding(0, dp(4), 0, dp(6));
        card.addView(technical);

        TextView reason = new TextView(this);
        reason.setText(field.unsupportedReason);
        reason.setTextSize(11f);
        reason.setTextColor(UiPalette.textSecondary(this));
        reason.setPadding(0, dp(4), 0, dp(6));
        card.addView(reason);

        if (state != null) {
            TextView stateText = new TextView(this);
            stateText.setText((fa ? "وضعیت تنظیم: " : "Stored state: ") + state.name());
            stateText.setTextSize(11f);
            stateText.setTextColor(UiPalette.textSecondary(this));
            card.addView(stateText);
        }

        if (!field.editable) {
            TextView readOnly = new TextView(this);
            readOnly.setText(fa ? "فقط خواندنی — این فیلد قابل تنظیم نیست." :
                    "Read-only — this field cannot be configured.");
            readOnly.setTextSize(12f);
            readOnly.setTextColor(UiPalette.textSecondary(this));
            card.addView(readOnly);
            return card;
        }

        View input;
        if (field.type == ProfileFieldRegistry.ValueType.BOOLEAN) {
            CheckBox check = new CheckBox(this);
            check.setText(fa ? "فعال / true" : "Enabled / true");
            check.setChecked(Boolean.TRUE.equals(storedValue));
            input = check;
        } else {
            EditText edit = new EditText(this);
            edit.setSingleLine(true);
            edit.setTextSize(14f);
            edit.setHint(field.validationRule);
            if (field.type == ProfileFieldRegistry.ValueType.INTEGER) {
                edit.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_SIGNED);
            } else if (field.type == ProfileFieldRegistry.ValueType.DECIMAL) {
                edit.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL
                        | InputType.TYPE_NUMBER_FLAG_SIGNED);
            } else {
                edit.setInputType(InputType.TYPE_CLASS_TEXT);
            }
            edit.setText(storedValue == null ? "" : String.valueOf(storedValue));
            input = edit;
        }
        card.addView(input);

        LinearLayout actions = new LinearLayout(this);
        actions.setOrientation(LinearLayout.HORIZONTAL);
        Button save = new Button(this);
        save.setAllCaps(false);
        save.setText(fa ? "ذخیره Override" : "Save Override");
        save.setOnClickListener(v -> saveField(field, input, card));
        actions.addView(save, new LinearLayout.LayoutParams(
                0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        Button reset = new Button(this);
        reset.setAllCaps(false);
        reset.setText(cloneMode
                ? (fa ? "استفاده از Global" : "Use Global")
                : (fa ? "پیش‌فرض امن" : "Safe Default"));
        reset.setOnClickListener(v -> resetField(field, card));
        actions.addView(reset, new LinearLayout.LayoutParams(
                0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        card.addView(actions);

        if (cloneMode && field.safeDefault != null) {
            Button safeDefault = new Button(this);
            safeDefault.setAllCaps(false);
            safeDefault.setText(fa ? "انتخاب Safe Default برای همین کلون" :
                    "Use Safe Default for this Clone");
            safeDefault.setOnClickListener(v -> setCloneSafeDefault(field, card));
            card.addView(safeDefault);
        }
        return card;
    }

    private void saveField(ProfileFieldRegistry.Field field, View input, View card) {
        Object value;
        try {
            if (field.type == ProfileFieldRegistry.ValueType.BOOLEAN) {
                value = ((CheckBox) input).isChecked();
            } else {
                String raw = ((EditText) input).getText().toString().trim();
                if (raw.isEmpty()) throw new IllegalArgumentException("A value is required");
                switch (field.type) {
                    case INTEGER: value = Long.valueOf(raw); break;
                    case DECIMAL: value = Double.valueOf(raw); break;
                    case STRING:
                    default: value = raw; break;
                }
            }
        } catch (RuntimeException invalid) {
            toast(fa ? "مقدار واردشده معتبر نیست." : "The entered value is invalid.");
            return;
        }
        if (!ProfileFieldRegistry.isValidValue(field, value)) {
            toast((fa ? "اعتبارسنجی ناموفق: " : "Validation failed: ") + field.validationRule);
            return;
        }
        if (isCoordinateCriticalField(field.key)) {
            ProfileDocument candidateClone = cloneDocument.copy();
            ProfileDocument candidateGlobal = globalDocument.copy();
            boolean accepted = cloneMode
                    ? candidateClone.put(field.key, value)
                    : candidateGlobal.put(field.key, value);
            if (!accepted || !validLocationConfiguration(candidateClone, candidateGlobal)) {
                toast(fa ? "برای فعال‌بودن موقعیت، طول و عرض جغرافیایی معتبر هر دو باید تنظیم شوند."
                        : "Enabled location requires both valid latitude and longitude values.");
                return;
            }
        }
        performMutation(card, callback -> {
            if (cloneMode) repository.saveCloneProfileField(packageName, userId, field.key, value, callback);
            else repository.saveGlobalProfileField(field.key, value, callback);
        });
    }

    private void resetField(ProfileFieldRegistry.Field field, View card) {
        if (isCoordinateCriticalField(field.key)) {
            ProfileDocument candidateClone = cloneDocument.copy();
            ProfileDocument candidateGlobal = globalDocument.copy();
            if (cloneMode) candidateClone.markInheritGlobal(field.key);
            else candidateGlobal.markSafeDefault(field.key);
            if (!validLocationConfiguration(candidateClone, candidateGlobal)) {
                toast(fa ? "ابتدا موقعیت را غیرفعال کنید یا مختصات کامل جایگزین کنید."
                        : "Disable location first or provide a complete replacement coordinate pair.");
                return;
            }
        }
        performMutation(card, callback -> {
            if (cloneMode) repository.clearCloneProfileDocumentField(packageName, userId, field.key, callback);
            else repository.clearGlobalProfileDocumentField(field.key, callback);
        });
    }

    private void setCloneSafeDefault(ProfileFieldRegistry.Field field, View card) {
        ProfileDocument candidateClone = cloneDocument.copy();
        candidateClone.markSafeDefault(field.key);
        if (isCoordinateCriticalField(field.key)
                && !validLocationConfiguration(candidateClone, globalDocument)) {
            toast(fa ? "پیش‌فرض امن موقعیت باید غیرفعال بماند." :
                    "The Safe Default must keep location disabled.");
            return;
        }
        performMutation(card, callback ->
                repository.setCloneProfileFieldSafeDefault(packageName, userId, field.key, callback));
    }

    private boolean isCoordinateCriticalField(String key) {
        return "locationEnabled".equals(key) || "latitude".equals(key) || "longitude".equals(key);
    }

    private boolean validLocationConfiguration(ProfileDocument candidateClone,
                                                ProfileDocument candidateGlobal) {
        Map<String, ProfileDocumentResolver.FieldResult> fields =
                ProfileDocumentResolver.resolveAll(candidateClone, candidateGlobal);
        Object enabled = fields.get("locationEnabled").value;
        if (!Boolean.TRUE.equals(enabled)) return true;
        return fields.get("latitude").value != null && fields.get("longitude").value != null;
    }

    private void performMutation(View card, Mutation mutation) {
        setCardEnabled(card, false);
        mutation.run(result -> {
            if (isFinishing() || isDestroyed()) return;
            if (!result.isSuccess() || !Boolean.TRUE.equals(result.getValue())) {
                setCardEnabled(card, true);
                toast((fa ? "ذخیره تغییر ناموفق بود: " : "Profile update failed: ")
                        + result.getMessage());
                return;
            }
            showLoading();
            loadDocuments();
        });
    }

    private void setCardEnabled(View view, boolean enabled) {
        view.setEnabled(enabled);
        if (view instanceof ViewGroup) {
            ViewGroup group = (ViewGroup) view;
            for (int i = 0; i < group.getChildCount(); i++) setCardEnabled(group.getChildAt(i), enabled);
        }
    }

    private void failLoad(String message) {
        loadFailed = true;
        if (!isFinishing() && !isDestroyed()) {
            showLoading();
            toast(message);
        }
    }

    private String displayCategory(String category) {
        if (!fa) return category;
        if ("Locale & Formatting".equals(category)) return "زبان و قالب‌بندی";
        if ("Location".equals(category)) return "موقعیت مکانی";
        if ("Device & OS".equals(category)) return "دستگاه و سیستم‌عامل";
        if ("Network".equals(category)) return "شبکه";
        if ("Identifiers & Services".equals(category)) return "شناسه‌ها و سرویس‌ها";
        if ("Browser & WebView".equals(category)) return "مرورگر و WebView";
        if ("App Data & Privacy".equals(category)) return "داده و حریم خصوصی برنامه";
        return category;
    }

    private String valueText(Object value) {
        return value == null ? (fa ? "بدون مقدار / تعریف‌نشده" : "Not configured") : String.valueOf(value);
    }

    private void toast(String message) {
        Toast.makeText(this, message, Toast.LENGTH_LONG).show();
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}
