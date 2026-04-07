[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "shared.ps1")

Push-Location (Get-RepoRoot)
try {
    & git config core.hooksPath .githooks
    Write-Host "Installed FPDS Git hooks with core.hooksPath=.githooks"
}
finally {
    Pop-Location
}
