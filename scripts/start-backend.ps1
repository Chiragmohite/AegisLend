$ErrorActionPreference='Stop'
$Root=Split-Path $PSScriptRoot -Parent
$Python=Join-Path $Root '.venv/Scripts/python.exe'
Push-Location (Join-Path $Root 'backend')
try { & $Python -m uvicorn app.main:create_app --factory --reload --host 127.0.0.1 --port 8000 --no-proxy-headers; if ($LASTEXITCODE -ne 0) { throw 'Backend exited with an error. Inspect output above.' } } finally { Pop-Location }
