# SQLite backup and restore

The local database contains sensitive N.E.X.U.S data, including conversations, memories, authentication records, skills, provider settings, tasks and audit metadata. Treat every backup as sensitive.

## Create a consistent backup

The backup helper uses SQLite's online backup API, so it creates a consistent snapshot even when the application is active:

```powershell
python -m nexus_learning.backup backup .\nexus_learning.db .\backups\nexus-2026-11-02.db
```

The destination is not overwritten by default. Use `--overwrite` only when intentionally replacing an existing backup. The helper validates the snapshot with `PRAGMA integrity_check` and attempts to restrict file permissions to the current owner (mode 0600 on POSIX systems; Windows inherits directory ACLs).

## Restore

**Stop the N.E.X.U.S API and worker before restoring.** Restoring over a database that is still open can fail on Windows or leave the running process using an old connection.

Restore into a new destination first when possible:

```powershell
python -m nexus_learning.backup restore .\backups\nexus-2026-11-02.db .\nexus-restored.db
```

To replace an existing database, both flags are required: `--overwrite` and a new, separate `--safety-backup` path. The existing database is copied and integrity-checked before replacement:

```powershell
python -m nexus_learning.backup restore .\backups\nexus-2026-11-02.db .\nexus_learning.db --overwrite --safety-backup .\backups\before-restore.db
```

The restore source is integrity-checked before any destination change. The restored temporary database is checked again before atomic replacement. Invalid snapshots are rejected. Symbolic-link paths are rejected.

## Operational limits

- This is a local SQLite file backup, not cloud synchronization or disaster recovery.
- Keep backups on a separate disk or encrypted storage; a backup beside the database does not protect against disk loss.
- Test restores periodically into a separate destination.
- Backups include private user data. Do not commit them, upload them to public repositories, or share them without authorization.
- The helper does not stop services, alter provider credentials, or perform automatic scheduled backups.
