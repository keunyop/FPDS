[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "shared.ps1")

$repoRoot = Get-RepoRoot
$packageJsonFiles = Get-ChildItem -Path $repoRoot -Recurse -Filter package.json -File | Where-Object {
    $_.FullName -notmatch "\\\.git\\" -and $_.FullName -notmatch "\\node_modules\\"
}

if (-not $packageJsonFiles) {
    Write-Host "No package.json files found. Skipping project checks."
    exit 0
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Error "package.json exists but npm is not available."
    exit 1
}

$scriptOrder = @("lint", "typecheck", "test", "build")

foreach ($packageJsonFile in ($packageJsonFiles | Sort-Object FullName)) {
    $relativePackagePath = Get-RepoRelativePath -AbsolutePath $packageJsonFile.FullName
    $packageJson = Get-Content -LiteralPath $packageJsonFile.FullName -Raw | ConvertFrom-Json
    $availableScripts = @()

    if ($packageJson.PSObject.Properties.Name -contains "scripts") {
        $availableScripts = @($packageJson.scripts.PSObject.Properties.Name)
    }

    if ($availableScripts.Count -eq 0) {
        Write-Host "No npm scripts found in $relativePackagePath. Skipping."
        continue
    }

    $packageDirectory = Split-Path -Parent $packageJsonFile.FullName
    Push-Location $packageDirectory
    try {
        foreach ($scriptName in $scriptOrder) {
            if ($availableScripts -contains $scriptName) {
                Write-Host "Running npm script in ${relativePackagePath}: $scriptName"
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
}
