$ErrorActionPreference='Stop'
$Root=Split-Path $PSScriptRoot -Parent
$Python=Join-Path $Root '.venv/Scripts/python.exe'
Push-Location (Join-Path $Root 'backend')
try { & $Python -m app.seed --confirm-demo; if ($LASTEXITCODE -ne 0) { throw 'Demo seed failed. Apply migrations and verify database settings first.' } } finally { Pop-Location }
