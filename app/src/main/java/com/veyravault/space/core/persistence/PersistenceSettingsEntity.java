package com.veyravault.space.core.persistence;

import androidx.room.Entity;
import androidx.room.PrimaryKey;

@Entity(tableName = "persistence_settings")
public class PersistenceSettingsEntity {
    @PrimaryKey public int id = 1;
    public boolean masterMockGpsEnabled = true;
}
