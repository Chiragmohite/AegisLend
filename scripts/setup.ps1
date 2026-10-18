param([ValidateSet('ExistingMySQL','FreshDocker')][string]$Mode='ExistingMySQL')
$ErrorActionPreference='Stop'
$Root=Split-Path $PSScriptRoot -Parent
Set-Location $Root
function Check([string]$What) { if ($LASTEXITCODE -ne 0) { throw "$What failed (exit $LASTEXITCODE). Resolve the error before continuing." } }
if ($Mode -eq 'FreshDocker' -and ((Test-Path '.env') -or (Test-Path 'backend/.env') -or (Test-Path 'frontend/.env'))) {
    throw 'FreshDocker requires a clean extracted project without local .env files. Existing environments: use ExistingMySQL; no credentials were changed.'
}
if (-not (Test-Path '.venv/Scripts/python.exe')) { py -3.12 -m venv .venv; Check 'Python 3.12 virtual environment creation' }
$Python=Join-Path $Root '.venv/Scripts/python.exe'
& $Python -m pip install -r backend/requirements.txt; Check 'Backend installation'
Push-Location frontend
try { npm ci; Check 'Frontend installation' } finally { Pop-Location }
if ($Mode -eq 'FreshDocker') {
    & $Python scripts/init_env.py; Check 'Environment initialization'
    & $Python -c "from pathlib import Path; p=Path('backend/.env'); p.write_text(p.read_text().replace('DB_PORT=3306','DB_PORT=3307'))"; Check 'Fresh isolated port configuration'
} else {
    if (-not (Test-Path 'backend/.env')) { Copy-Item backend/.env.example backend/.env }
    if (-not (Test-Path 'frontend/.env')) { Copy-Item frontend/.env.example frontend/.env }
}
if (-not (Select-String -Path backend/.env -Pattern '^\s*(export\s+)?JWT_SECRET\s*=' -Quiet)) {
    if (-not $env:JWT_SECRET) { & $Python scripts/configure_auth.py; Check 'JWT signing key configuration' }
}
if ($Mode -eq 'FreshDocker') { docker compose -f compose.fresh.yaml up -d --wait mysql; Check 'Isolated MySQL startup' }
Write-Host 'Dependencies ready. ExistingMySQL: set your actual DB_* values in backend/.env before migrating. No existing database was reset.'
