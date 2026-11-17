package com.veyravault.space.core.persistence;

import androidx.annotation.NonNull;
import androidx.room.Entity;
import androidx.room.PrimaryKey;

@Entity(tableName = "last_active_launch")
public class LastActiveLaunchEntity {
    @PrimaryKey public int id = 1;
    // Intentionally no FK: legacy storage can retain a stale marker after clone removal.
    @NonNull public String packageName = "";
    public int userId;
}
