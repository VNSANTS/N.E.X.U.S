"""Minimal, non-overriding loader for a project-local .env file."""
import os
import re
from pathlib import Path

_NAME=re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
def load_local_env(project_root=None):
    root=Path(project_root) if project_root is not None else Path(__file__).resolve().parent.parent
    path=root/'.env'
    if not path.exists(): return False
    if path.is_symlink() or not path.is_file() or path.stat().st_size>64_000:
        raise ValueError('unsafe or oversized local environment file')
    content=path.read_text(encoding='utf-8')
    for line in content.splitlines():
        stripped=line.strip()
        if not stripped or stripped.startswith('#'): continue
        if '=' not in stripped: continue
        name,value=stripped.split('=',1); name=name.strip(); value=value.strip()
        if not _NAME.fullmatch(name): continue
        if len(value)>=2 and value[0]==value[-1] and value[0] in {'"',"'"}: value=value[1:-1]
        if name not in os.environ: os.environ[name]=value
    return True
