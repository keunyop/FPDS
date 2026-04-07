[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "shared.ps1")

$stagedFiles = Get-StagedFiles
if (-not $stagedFiles -or $stagedFiles.Count -eq 0) {
    exit 0
}

foreach ($relativePath in $stagedFiles) {
    if (Test-TextFilePath -RelativePath $relativePath) {
        Invoke-TextAutoFix -RelativePath $relativePath | Out-Null
    }
}

$findings = [System.Collections.Generic.List[object]]::new()
$markdownFiles = @($stagedFiles | Where-Object { $_.EndsWith(".md", [System.StringComparison]::OrdinalIgnoreCase) })
$powerShellFiles = @($stagedFiles | Where-Object { $_.EndsWith(".ps1", [System.StringComparison]::OrdinalIgnoreCase) })

if ($markdownFiles.Count -gt 0) {
    foreach ($finding in Get-MarkdownReferenceFindings -RelativePaths $markdownFiles) {
        $findings.Add($finding)
    }
}

if ($powerShellFiles.Count -gt 0) {
    foreach ($finding in Get-PowerShellSyntaxFindings -RelativePaths $powerShellFiles) {
        $findings.Add($finding)
    }
}

if ($findings.Count -gt 0) {
    Write-Findings -Findings $findings.ToArray()
    exit 1
}

exit 0
