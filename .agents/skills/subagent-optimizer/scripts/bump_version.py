#!/usr/bin/env python3
"""Bump (or set) the `version` field in an agent file's frontmatter.

Run this on each agent AFTER its optimisations are applied and approved.

Rules:
  - No `version` field present  -> insert `version: 1.1.0`
    (the unversioned baseline is treated as 1.0.0; optimisation is a minor bump).
  - `version: X.Y.Z` present    -> minor bump -> `X.(Y+1).0` (quotes and a `v`
    prefix are accepted and preserved).
  - `--set X.Y.Z`               -> force that exact version.
  - A `version:` line that does not parse, frontmatter that does not start on
    line 1, or a symlink -> SKIP, file untouched.
  - A Codex agent (.toml) -> REFUSE, file untouched, exit code 1: Codex agent
    files have no version field and Codex skips an agent with an unknown key.

The field is inserted right after the `name:` line so it stays visible. Line
endings are preserved (a leading BOM is not) and the file is replaced atomically.

Usage:
    python bump_version.py AGENT.md [AGENT.md ...] [--set X.Y.Z] [--dry-run]
Exit code is 1 if any path could not be read or written, or was refused.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from pathlib import Path

VER_RE = re.compile(
    r"""^version:\s*(?P<q>["']?)(?P<v>v?)(\d+)\.(\d+)(?:\.(\d+))?(?P=q)\s*$""")
ANY_VER_RE = re.compile(r"^version:")


def bump(major: int, minor: int) -> str:
    return f"{major}.{minor + 1}.0"


REFUSE_PREFIX = "REFUSE"


def process(path: Path, force: str | None, dry: bool) -> str:
    if path.suffix == ".toml":
        return (f"{REFUSE_PREFIX} {path.name}: Codex agent files have no version field and "
                "Codex skips an agent with an unknown key; not bumped")
    if path.is_symlink():
        return f"SKIP {path.name}: refusing to follow a symlink"
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        text = fh.read()
    lines = text.splitlines(keepends=True)
    fences = [i for i, l in enumerate(lines) if l.strip() == "---"]
    if len(fences) < 2 or fences[0] != 0:
        return f"SKIP {path.name}: no frontmatter"
    start, end = fences[0], fences[1]
    eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

    ver_idx = None
    for i in range(start + 1, end):
        if ANY_VER_RE.match(lines[i]):
            if not VER_RE.match(lines[i]):
                return f"SKIP {path.name}: unparsable version line {lines[i].strip()!r}"
            ver_idx = i
            break

    quote, prefix = "", ""
    if ver_idx is not None:
        m = VER_RE.match(lines[ver_idx])
        quote, prefix = m.group("q"), m.group("v")
        new_ver = force or bump(int(m.group(3)), int(m.group(4)))
        old = lines[ver_idx].strip().split(":", 1)[1].strip()
        new_lines = list(lines)
        new_lines[ver_idx] = f"version: {quote}{prefix}{new_ver}{quote}{eol}"
    else:
        new_ver = force or "1.1.0"
        old = "(none)"
        insert_at = start + 1
        for i in range(start + 1, end):
            if re.match(r"^name:\s", lines[i]):
                insert_at = i + 1
                break
        new_lines = lines[:insert_at] + [f"version: {new_ver}{eol}"] + lines[insert_at:]

    if dry:
        return f"DRY  {path.name}: {old} -> {new_ver}"
    # A fresh, exclusively created temp file in the same directory: a pre-planted
    # symlink at a predictable name cannot redirect the write.
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
            fh.write("".join(new_lines))
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return f"OK   {path.name}: {old} -> {new_ver}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+", help="agent .md files")
    ap.add_argument("--set", dest="force", help="force exact version X.Y.Z")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if args.force and not re.fullmatch(r"\d+\.\d+\.\d+", args.force):
        sys.exit("--set must be X.Y.Z")
    failed = False
    for p in args.paths:
        path = Path(p).expanduser()
        try:
            result = process(path, args.force, args.dry_run)
            print(result)
            failed = failed or result.startswith(REFUSE_PREFIX)
        except (OSError, UnicodeDecodeError) as exc:
            failed = True
            print(f"ERROR {path.name}: {exc}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
