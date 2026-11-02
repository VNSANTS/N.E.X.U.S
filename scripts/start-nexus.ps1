Set-Location (Split-Path -Parent $PSScriptRoot)
python -m nexus_learning --db nexus_learning.db serve --host 127.0.0.1 --port 8765
