[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "shared.ps1")

function Test-PackageManagerPreference {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PackageDirectory,
        [Parameter(Mandatory = $true)]
        [object]$PackageJson
    )

    if ($PackageJson.PSObject.Properties.Name -contains "packageManager") {
        $packageManagerValue = [string]$PackageJson.packageManager
        if ($packageManagerValue.StartsWith("pnpm@", [System.StringComparison]::OrdinalIgnoreCase)) {
            return "pnpm"
        }
        if ($packageManagerValue.StartsWith("npm@", [System.StringComparison]::OrdinalIgnoreCase)) {
            return "npm"
        }
    }

    $pnpmLockPath = Join-Path $PackageDirectory "pnpm-lock.yaml"
    if (Test-Path -LiteralPath $pnpmLockPath) {
        return "pnpm"
    }

    $npmLockCandidates = @(
        (Join-Path $PackageDirectory "package-lock.json"),
        (Join-Path $PackageDirectory "npm-shrinkwrap.json")
    )
    foreach ($candidate in $npmLockCandidates) {
        if (Test-Path -LiteralPath $candidate) {
            return "npm"
        }
    }

    if (Get-Command pnpm -ErrorAction SilentlyContinue) {
        return "pnpm"
    }

    return "npm"
}

function Get-RunCommandParts {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PackageManager
    )

    switch ($PackageManager) {
        "pnpm" {
            if (Get-Command pnpm -ErrorAction SilentlyContinue) {
                return @{
                    Command = "pnpm"
                    Prefix  = @("run")
                }
            }

            if (Get-Command corepack -ErrorAction SilentlyContinue) {
                return @{
                    Command = "corepack"
                    Prefix  = @("pnpm", "run")
                }
            }

            throw "Package checks need pnpm, but neither 'pnpm' nor 'corepack' is available."
        }
        "npm" {
            if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
                throw "Package checks need npm, but 'npm' is not available."
            }

            return @{
                Command = "npm"
                Prefix  = @("run")
            }
        }
        default {
            throw "Unsupported package manager preference '$PackageManager'."
        }
    }
}

$repoRoot = Get-RepoRoot
$packageJsonFiles = Get-ChildItem -Path $repoRoot -Recurse -Filter package.json -File | Where-Object {
    $_.FullName -notmatch "\\\.git\\" -and $_.FullName -notmatch "\\node_modules\\"
}

if (-not $packageJsonFiles) {
    Write-Host "No package.json files found. Skipping project checks."
    exit 0
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
    $packageManagerPreference = Test-PackageManagerPreference -PackageDirectory $packageDirectory -PackageJson $packageJson
    $runCommandParts = Get-RunCommandParts -PackageManager $packageManagerPreference
    Push-Location $packageDirectory
    try {
        foreach ($scriptName in $scriptOrder) {
            if ($availableScripts -contains $scriptName) {
                Write-Host "Running ${packageManagerPreference} script in ${relativePackagePath}: $scriptName"
                & $runCommandParts.Command @($runCommandParts.Prefix + @($scriptName))
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
