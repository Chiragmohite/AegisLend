$ErrorActionPreference='Stop'
$Root=Split-Path $PSScriptRoot -Parent
Push-Location (Join-Path $Root 'frontend')
try { npm run dev; if ($LASTEXITCODE -ne 0) { throw 'Frontend exited with an error. Inspect output above.' } } finally { Pop-Location }
