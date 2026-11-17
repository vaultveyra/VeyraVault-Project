package com.veyravault.space.core.persistence;

import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.OnConflictStrategy;
import androidx.room.Query;
import java.util.List;

@Dao
public interface DeniedPermissionDao {
    @Query("SELECT * FROM clone_denied_permissions WHERE packageName = :packageName AND userId = :userId ORDER BY permission ASC")
    List<DeniedPermissionEntity> getForClone(String packageName, int userId);

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    void insertOrReplaceAll(List<DeniedPermissionEntity> permissions);

    @Query("DELETE FROM clone_denied_permissions WHERE packageName = :packageName AND userId = :userId")
    void deleteForClone(String packageName, int userId);

    @Query("SELECT * FROM clone_denied_permissions ORDER BY packageName ASC, userId ASC, permission ASC")
    List<DeniedPermissionEntity> getAll();

    @Query("SELECT COUNT(*) FROM clone_denied_permissions")
    int count();

    @Query("DELETE FROM clone_denied_permissions")
    void deleteAll();
}
