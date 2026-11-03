"""Safe SQLite backup/restore helpers for the local N.E.X.U.S database.

Backups contain sensitive application data. Store them offline and protect access.
"""
import argparse
import os
import sqlite3
import tempfile
from pathlib import Path


def _database_file(value, *, must_exist):
    raw_path = Path(value).expanduser()
    if raw_path.is_symlink():
        raise ValueError("symbolic links are not accepted for database paths")
    path = raw_path.resolve()
    if must_exist and not path.is_file():
        raise FileNotFoundError("database file does not exist or is not a regular file")
    if not must_exist and path.exists() and path.is_dir():
        raise IsADirectoryError(str(path))
    return path


def _integrity_check(path):
    connection = sqlite3.connect(str(path), timeout=10)
    try:
        result = connection.execute("PRAGMA integrity_check").fetchone()
        if not result or result[0] != "ok":
            raise sqlite3.DatabaseError("SQLite integrity check failed")
    finally:
        connection.close()


def _snapshot(source, temporary):
    src = sqlite3.connect(str(source), timeout=10)
    dst = sqlite3.connect(str(temporary), timeout=10)
    try:
        src.backup(dst)
        dst.commit()
    finally:
        dst.close()
        src.close()
    _integrity_check(temporary)
    try:
        os.chmod(temporary, 0o600)
    except OSError:
        # Windows ACLs are inherited from the destination directory.
        pass


def backup_database(source, destination, *, overwrite=False):
    """Create a consistent SQLite snapshot; never overwrite unless requested."""
    src = _database_file(source, must_exist=True)
    dst = _database_file(destination, must_exist=False)
    if src == dst:
        raise ValueError("source and destination must be different files")
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and not overwrite:
        raise FileExistsError(str(dst))
    fd, temporary_name = tempfile.mkstemp(prefix=".nexus-backup-", suffix=".tmp",
                                          dir=str(dst.parent))
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        _snapshot(src, temporary)
        if not overwrite and dst.exists():
            raise FileExistsError(str(dst))
        os.replace(temporary, dst)
        return dst
    finally:
        temporary.unlink(missing_ok=True)


def restore_database(backup, destination, *, overwrite=False, safety_backup=None):
    """Restore a validated snapshot; overwrites require a separate safety copy."""
    src = _database_file(backup, must_exist=True)
    dst = _database_file(destination, must_exist=False)
    if src == dst:
        raise ValueError("backup and destination must be different files")
    _integrity_check(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        if not overwrite:
            raise FileExistsError(str(dst))
        if safety_backup is None:
            raise ValueError("overwriting requires a separate safety_backup path")
        safety = _database_file(safety_backup, must_exist=False)
        if safety in {src, dst}:
            raise ValueError("safety backup must be a different file")
        backup_database(dst, safety, overwrite=False)
    elif safety_backup is not None:
        raise ValueError("safety_backup is only valid when replacing an existing database")

    fd, temporary_name = tempfile.mkstemp(prefix=".nexus-restore-", suffix=".tmp",
                                          dir=str(dst.parent))
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        _snapshot(src, temporary)
        os.replace(temporary, dst)
        return dst
    finally:
        temporary.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Create or restore a safe N.E.X.U.S SQLite snapshot.")
    sub = parser.add_subparsers(dest="command", required=True)
    backup = sub.add_parser("backup", help="create a consistent SQLite backup")
    backup.add_argument("source")
    backup.add_argument("destination")
    backup.add_argument("--overwrite", action="store_true")
    restore = sub.add_parser("restore", help="restore a validated SQLite backup")
    restore.add_argument("backup")
    restore.add_argument("destination")
    restore.add_argument("--overwrite", action="store_true")
    restore.add_argument("--safety-backup")
    args = parser.parse_args(argv)
    if args.command == "backup":
        path = backup_database(args.source, args.destination, overwrite=args.overwrite)
    else:
        path = restore_database(args.backup, args.destination, overwrite=args.overwrite,
                                safety_backup=args.safety_backup)
    print(f"SQLite snapshot ready: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
