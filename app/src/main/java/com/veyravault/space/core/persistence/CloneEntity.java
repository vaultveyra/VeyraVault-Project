package com.veyravault.space.core.persistence;

import androidx.annotation.NonNull;
import androidx.room.Entity;
import androidx.room.PrimaryKey;

@Entity(tableName = "clones", primaryKeys = {"packageName", "userId"})
public class CloneEntity {
    @NonNull public String packageName = "";
    public int userId;
    public String displayName;
    public boolean mockGpsEnabled;
    public double latitude;
    public double longitude;
    public String locationLabel;
    public boolean customDeviceEnabled;
    public String deviceBrand;
    public String deviceModel;
    // Exact source JSON retains unknown legacy fields across migration.
    @NonNull public String legacyJson = "{}";
}
