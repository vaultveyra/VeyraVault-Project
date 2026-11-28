package com.veyravault.space.core;

import android.content.Context;
import android.content.SharedPreferences;

import androidx.test.core.app.ApplicationProvider;
import androidx.test.ext.junit.runners.AndroidJUnit4;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;

import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

@RunWith(AndroidJUnit4.class)
public class CloneUserIdScopeInstrumentationTest {
    private static final String PREFS = "veyravault_clones_v2";

    private Context context;
    private SharedPreferences prefs;
    private Map<String, ?> before;

    @Before public void setUp() {
        context = ApplicationProvider.getApplicationContext();
        prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        before = copySnapshot(prefs.getAll());
        assertTrue("Synthetic CloneStore preferences must be isolated for this test",
                prefs.edit().clear().commit());
    }

    @After public void tearDown() {
        restorePreferences(prefs, before);
    }

    @Test public void globalAllocatorNeverReservesSameNumericUserIdForDifferentPackages() throws Exception {
        // These are synthetic package identities. No Engine install or app data is created.
        CloneStore.CloneReservation alpha =
                CloneStore.reserveNextUserId(context, "com.example.synthetic.alpha",
                        Collections.<Integer>emptyList(), Collections.<Integer>emptyList());
        CloneStore.CloneReservation beta =
                CloneStore.reserveNextUserId(context, "com.example.synthetic.beta",
                        Collections.<Integer>emptyList(), Collections.<Integer>emptyList());
        CloneStore.CloneReservation alphaSecond =
                CloneStore.reserveNextUserId(context, "com.example.synthetic.alpha",
                        Collections.<Integer>emptyList(), Collections.<Integer>emptyList());

        assertTrue(!alpha.getPackageName().equals(beta.getPackageName()));
        assertEquals(0, alpha.getUserId());
        assertEquals(1, beta.getUserId());
        assertEquals(2, alphaSecond.getUserId());
        assertEquals(2, prefs.getInt("last_reserved_global_user_id", -1));

        // The journal is restored to its pre-test key/value snapshot in @After.
        assertEquals(3, CloneStore.readPendingReservationsStrict(context).size());
    }

    @Test public void removedCloneRegistryEntryDoesNotLowerGlobalHighWaterMark() {
        String packageName = "com.example.synthetic.recreated";
        CloneStore.CloneEntry entry = new CloneStore.CloneEntry();
        entry.packageName = packageName;
        entry.userId = 0;
        entry.displayName = "Synthetic Clone";

        assertTrue(CloneStore.upsertClone(context, entry));
        CloneStore.CloneReservation first = CloneStore.reserveNextUserId(context, packageName,
                Collections.singletonList(0), Collections.<Integer>emptyList());
        assertEquals(1, first.getUserId());

        // This removes only the synthetic registry entry. It does not call Engine or
        // delete any app/account data; the high-water mark must remain advanced.
        assertTrue(CloneStore.removeClone(context, packageName, 0));
        CloneStore.CloneReservation next = CloneStore.reserveNextUserId(context, packageName,
                Collections.singletonList(0), Collections.<Integer>emptyList());
        assertEquals(2, next.getUserId());
        assertEquals(2, prefs.getInt("last_reserved_global_user_id", -1));
    }

    private static Map<String, ?> copySnapshot(Map<String, ?> source) {
        Map<String, Object> copy = new HashMap<>();
        for (Map.Entry<String, ?> entry : source.entrySet()) {
            Object value = entry.getValue();
            if (value instanceof Set) {
                @SuppressWarnings("unchecked")
                Set<String> strings = new HashSet<>((Set<String>) value);
                copy.put(entry.getKey(), strings);
            } else {
                copy.put(entry.getKey(), value);
            }
        }
        return copy;
    }

    private static void restorePreferences(SharedPreferences preferences, Map<String, ?> snapshot) {
        SharedPreferences.Editor editor = preferences.edit().clear();
        if (snapshot != null) {
            for (Map.Entry<String, ?> entry : snapshot.entrySet()) {
                Object value = entry.getValue();
                String key = entry.getKey();
                if (value instanceof String) editor.putString(key, (String) value);
                else if (value instanceof Boolean) editor.putBoolean(key, (Boolean) value);
                else if (value instanceof Integer) editor.putInt(key, (Integer) value);
                else if (value instanceof Long) editor.putLong(key, (Long) value);
                else if (value instanceof Float) editor.putFloat(key, (Float) value);
                else if (value instanceof Set) {
                    @SuppressWarnings("unchecked")
                    Set<String> strings = new HashSet<>((Set<String>) value);
                    editor.putStringSet(key, strings);
                } else {
                    throw new AssertionError("Unexpected CloneStore preference type: "
                            + (value == null ? "null" : value.getClass().getName()));
                }
            }
        }
        assertTrue("CloneStore preferences must be restored after the synthetic test",
                editor.commit());
    }
}
