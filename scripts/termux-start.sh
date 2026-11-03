#!/data/data/com.termux/files/usr/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
DB_PATH=${NEXUS_DB_PATH:-"$HOME/nexus-data/nexus_learning.db"}
mkdir -p "$(dirname -- "$DB_PATH")"
chmod 700 "$(dirname -- "$DB_PATH")"
cd "$ROOT"

python - <<'PY'
import sys
if sys.version_info < (3, 11):
    raise SystemExit("N.E.X.U.S requires Python 3.11 or newer.")
print("Python", sys.version.split()[0])
PY

if [ ! -f .env ]; then
  echo "WARNING: .env is missing. Remote providers and integrations will remain unavailable."
fi

if command -v termux-wake-lock >/dev/null 2>&1; then
  termux-wake-lock || true
fi

echo "Starting N.E.X.U.S on 127.0.0.1:8765"
echo "SQLite database: $DB_PATH"
exec python -m nexus_learning --db "$DB_PATH" serve --host 127.0.0.1 --port 8765
