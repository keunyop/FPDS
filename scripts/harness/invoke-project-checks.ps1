[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "shared.ps1")

$repoRoot = Get-RepoRoot
$packageJsonPath = Join-Path $repoRoot "package.json"

if (-not (Test-Path -LiteralPath $packageJsonPath)) {
    Write-Host "No package.json found. Skipping project checks."
    exit 0
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Error "package.json exists but npm is not available."
    exit 1
}

$packageJson = Get-Content -LiteralPath $packageJsonPath -Raw | ConvertFrom-Json
$availableScripts = @()

if ($packageJson.PSObject.Properties.Name -contains "scripts") {
    $availableScripts = @($packageJson.scripts.PSObject.Properties.Name)
}

$scriptOrder = @("lint", "typecheck", "test", "build")

Push-Location $repoRoot
try {
    foreach ($scriptName in $scriptOrder) {
        if ($availableScripts -contains $scriptName) {
            Write-Host "Running npm script: $scriptName"
            & npm run $scriptName
            if ($LASTEXITCODE -ne 0) {
                exit $LASTEXITCODE
            }
        }
    }
}
finally {
    Pop-Location
}
