package com.veyravault.space.core.persistence;

import androidx.annotation.NonNull;
import androidx.room.Entity;
import androidx.room.PrimaryKey;

/**
 * Provenance and lossless source envelope for the one-time legacy import.
 * The canonical payload retains exact source JSON and key-presence semantics.
 */
@Entity(tableName = "legacy_migration_metadata")
public class LegacyMigrationMetadataEntity {
    @PrimaryKey public int id = 1;
    @NonNull public String sourceSnapshotSha256 = "";
    @NonNull public String sourceSnapshotPayload = "";
    public int sourceFormatVersion = 1;
}
