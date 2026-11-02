Set-Location (Split-Path -Parent $PSScriptRoot)
python -m nexus_learning --db nexus_learning.db worker --poll 1
