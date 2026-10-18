$ErrorActionPreference='Stop'
$Root=Split-Path $PSScriptRoot -Parent
$Python=Join-Path $Root '.venv/Scripts/python.exe'
Push-Location (Join-Path $Root 'backend')
try {
    & $Python -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) { throw 'Migration failed. Check MySQL connectivity and backend/.env. Do not reset an existing database.' }
    & $Python -m alembic current
    if ($LASTEXITCODE -ne 0) { throw 'Could not read migration revision.' }
} finally { Pop-Location }
