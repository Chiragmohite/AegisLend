$ErrorActionPreference='Stop'
$Root=Split-Path $PSScriptRoot -Parent
$Python=Join-Path $Root '.venv/Scripts/python.exe'
function Check([string]$What) { if ($LASTEXITCODE -ne 0) { throw "$What failed (exit $LASTEXITCODE)." } }
Push-Location (Join-Path $Root 'backend')
try {
    & $Python -m compileall -q app tests alembic; Check 'Python compilation'
    & $Python -m pip check; Check 'Dependency consistency'
    & $Python -m pytest -q; Check 'Backend tests'
} finally { Pop-Location }
Push-Location (Join-Path $Root 'frontend')
try { npm test; Check 'Frontend tests'; npm run build; Check 'TypeScript and frontend build' } finally { Pop-Location }
