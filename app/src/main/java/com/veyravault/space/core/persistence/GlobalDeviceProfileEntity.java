package com.veyravault.space.core.persistence;

import androidx.annotation.NonNull;
import androidx.room.Entity;
import androidx.room.PrimaryKey;

@Entity(tableName = "global_device_profile")
public class GlobalDeviceProfileEntity {
    @PrimaryKey public int id = 1;
    public boolean enabled = true;
    @NonNull public String brand = "samsung";
    @NonNull public String manufacturer = "samsung";
    @NonNull public String model = "SM-S928B";
    @NonNull public String device = "e3q";
    @NonNull public String countryIso = "us";
    @NonNull public String simOperator = "310260";
    @NonNull public String simOperatorName = "T-Mobile";
}
