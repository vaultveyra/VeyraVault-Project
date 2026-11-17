package com.veyravault.space.core.persistence;

import androidx.annotation.NonNull;
import androidx.room.Entity;
import androidx.room.PrimaryKey;

@Entity(tableName = "collapsed_spaces")
public class CollapsedSpaceEntity {
    // Keep the original String representation; do not normalize legacy values during import.
    @NonNull @PrimaryKey public String spaceKey = "";
}
