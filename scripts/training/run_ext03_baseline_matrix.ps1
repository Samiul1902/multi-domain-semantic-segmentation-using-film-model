# EXT-03 same-protocol baseline matrix launcher (project venv only).
# Usage:  powershell -File scripts\training\run_ext03_baseline_matrix.ps1 [-Resume]
param([switch]$Resume)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$Runner = Join-Path $RepoRoot "scripts\training\run_ext03_baseline_matrix.py"
$LogDir = Join-Path $RepoRoot "reports\baselines\logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Log = Join-Path $LogDir ("ext03_matrix_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".log")

$argList = @($Runner)
if ($Resume) { $argList += "--resume" }

Write-Host "Using interpreter: $Python"
Write-Host "Logging to: $Log"
& $Python @argList 2>&1 | Tee-Object -FilePath $Log
exit $LASTEXITCODE
