package com.veyravault.space.core.persistence;

import android.content.Context;
import androidx.room.Room;

/**
 * Opt-in Room database provider. Not called by application startup or CloneStore yet.
 * No destructive migration fallback is configured.
 */
public final class ClonePersistenceDatabaseProvider {
    private static volatile ClonePersistenceDatabase instance;

    private ClonePersistenceDatabaseProvider() { }

    public static ClonePersistenceDatabase get(Context context) {
        ClonePersistenceDatabase current = instance;
        if (current == null) {
            synchronized (ClonePersistenceDatabaseProvider.class) {
                current = instance;
                if (current == null) {
                    current = Room.databaseBuilder(
                        context.getApplicationContext(),
                        ClonePersistenceDatabase.class,
                        "veyravault_clone_store_room.db"
                    ).build();
                    instance = current;
                }
            }
        }
        return current;
    }
}
