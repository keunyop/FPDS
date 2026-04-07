[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "shared.ps1")

$findings = [System.Collections.Generic.List[object]]::new()

foreach ($finding in Get-HarnessMissingFileFindings) {
    $findings.Add($finding)
}

$markdownFiles = Get-MarkdownFilesUnderRepo
foreach ($finding in Get-MarkdownReferenceFindings -RelativePaths $markdownFiles) {
    $findings.Add($finding)
}

$powerShellFiles = Get-PowerShellFilesUnderRepo
foreach ($finding in Get-PowerShellSyntaxFindings -RelativePaths $powerShellFiles) {
    $findings.Add($finding)
}

if ($findings.Count -gt 0) {
    Write-Findings -Findings $findings.ToArray()
    exit 1
}

Write-Host "Repo doctor passed."
