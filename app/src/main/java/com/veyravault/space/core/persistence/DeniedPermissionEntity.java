package com.veyravault.space.core.persistence;

import androidx.annotation.NonNull;
import androidx.room.Entity;
import androidx.room.ForeignKey;
import androidx.room.Index;

@Entity(
    tableName = "clone_denied_permissions",
    primaryKeys = {"packageName", "userId", "permission"},
    foreignKeys = @ForeignKey(
        entity = CloneEntity.class,
        parentColumns = {"packageName", "userId"},
        childColumns = {"packageName", "userId"},
        onDelete = ForeignKey.CASCADE
    ),
    indices = {@Index(value = {"packageName", "userId"})}
)
public class DeniedPermissionEntity {
    @NonNull public String packageName = "";
    public int userId;
    @NonNull public String permission = "";
}
