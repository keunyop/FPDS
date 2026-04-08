[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptRoot = $PSScriptRoot

& (Join-Path $scriptRoot "repo-doctor.ps1")
& (Join-Path $scriptRoot "validate-foundation-baseline.ps1")
& (Join-Path $scriptRoot "invoke-project-checks.ps1")
