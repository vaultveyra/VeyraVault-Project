package com.veyravault.space.core;

import android.content.Context;
import android.content.SharedPreferences;

import androidx.test.core.app.ApplicationProvider;
import androidx.test.ext.junit.runners.AndroidJUnit4;

import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;

import static org.junit.Assert.*;

@RunWith(AndroidJUnit4.class)
public class CloneStoreSafetyInstrumentationTest {
    private static final String PREFS = "veyravault_clones_v2";
    private static final String KEY_CLONES = "clones_json";
    private Context context;
    private SharedPreferences prefs;

    @Before public void setUp() {
        context = ApplicationProvider.getApplicationContext();
        prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        assertTrue(prefs.edit().clear().commit());
    }

    @Test public void malformedRegistryBlocksMutationAndUserIdAllocationWithoutChangingBytes() {
        String malformed = "{not-json";
        assertTrue(prefs.edit().putString(KEY_CLONES, malformed).commit());

        CloneStore.CloneEntry entry = new CloneStore.CloneEntry();
        entry.packageName = "com.example.safe";
        entry.userId = 0;
        entry.displayName = "Safe";

        assertFalse(CloneStore.upsertClone(context, entry));
        assertFalse(CloneStore.removeClone(context, "com.example.safe", 0));
        assertEquals(-1, CloneStore.nextFreeUserIdForPackage(context, "com.example.safe"));
        assertEquals(malformed, prefs.getString(KEY_CLONES, null));
    }

    @Test public void duplicateCompositeIdentityBlocksMutationAndAllocation() {
        String duplicate = "["
                + "{\"pkg\":\"com.example.duplicate\",\"uid\":4},"
                + "{\"pkg\":\"com.example.duplicate\",\"uid\":4}"
                + "]";
        assertTrue(prefs.edit().putString(KEY_CLONES, duplicate).commit());

        CloneStore.CloneEntry entry = new CloneStore.CloneEntry();
        entry.packageName = "com.example.other";
        entry.userId = 0;
        entry.displayName = "Other";

        assertFalse(CloneStore.upsertClone(context, entry));
        assertEquals(-1, CloneStore.nextFreeUserIdForPackage(context, "com.example.other"));
        assertEquals(duplicate, prefs.getString(KEY_CLONES, null));
    }

    @Test public void invalidEnabledCoordinatesAreNotPersisted() {
        CloneStore.CloneEntry entry = new CloneStore.CloneEntry();
        entry.packageName = "com.example.invalidgps";
        entry.userId = 0;
        entry.displayName = "Invalid GPS";
        entry.mockGpsEnabled = true;
        entry.latitude = 91.0d;
        entry.longitude = 0.0d;

        assertFalse(CloneStore.upsertClone(context, entry));
        assertFalse(prefs.contains(KEY_CLONES));
    }

    @Test public void validRegistryMutationsReturnCommitStatusAndPreserveCompositeIdentity() {
        CloneStore.CloneEntry first = new CloneStore.CloneEntry();
        first.packageName = "com.example.shared";
        first.userId = 0;
        first.displayName = "Space One";
        CloneStore.CloneEntry second = new CloneStore.CloneEntry();
        second.packageName = "com.example.shared";
        second.userId = 1;
        second.displayName = "Space Two";

        assertTrue(CloneStore.upsertClone(context, first));
        assertTrue(CloneStore.upsertClone(context, second));
        assertEquals(2, CloneStore.getAll(context).size());
        assertEquals(2, CloneStore.nextFreeUserIdForPackage(context, "com.example.shared"));
        assertTrue(CloneStore.removeClone(context, "com.example.shared", 0));
        assertEquals(1, CloneStore.getAll(context).size());
        assertEquals(1, CloneStore.getAll(context).get(0).userId);
    }
}
