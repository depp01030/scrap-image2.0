$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ConfigPath = Join-Path $RepoRoot "config.json"
$AppDir = Join-Path $RepoRoot "src\\local_service"

if (Test-Path (Join-Path $RepoRoot ".venv\\Scripts\\python.exe")) {
    $PythonCommand = @(Join-Path $RepoRoot ".venv\\Scripts\\python.exe")
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonCommand = @("python")
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonCommand = @("py", "-3")
} else {
    throw "Cannot find Python. Install Python or create .venv in the project folder."
}

$Port = 8765
if (Test-Path $ConfigPath) {
    $Config = Get-Content -Raw $ConfigPath | ConvertFrom-Json
    if ($null -ne $Config.port) {
        $Port = [int]$Config.port
    }
}

Write-Host "Repo root: $RepoRoot"
Write-Host "App dir:   $AppDir"
Write-Host "Port:      $Port"
Write-Host "Python:    $($PythonCommand -join ' ')"

Push-Location $RepoRoot
try {
    $PythonExe = $PythonCommand[0]
    $PythonArgs = @()
    if ($PythonCommand.Length -gt 1) {
        $PythonArgs = $PythonCommand[1..($PythonCommand.Length - 1)]
    }
    & $PythonExe @PythonArgs -m uvicorn app.main:app --app-dir $AppDir --host 127.0.0.1 --port $Port
} finally {
    Pop-Location
}
