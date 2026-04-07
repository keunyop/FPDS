[CmdletBinding()]
param(
    [string]$ReportPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "shared.ps1")

$allTextFiles = Get-TextFilesUnderRepo
$markdownFiles = Get-MarkdownFilesUnderRepo

$findings = [System.Collections.Generic.List[object]]::new()
foreach ($finding in Get-HarnessMissingFileFindings) {
    $findings.Add($finding)
}
foreach ($finding in Get-MarkdownReferenceFindings -RelativePaths $markdownFiles) {
    $findings.Add($finding)
}
foreach ($finding in Get-TrailingWhitespaceFindings -RelativePaths $allTextFiles) {
    $findings.Add($finding)
}
foreach ($finding in Get-TodoFindings -RelativePaths $allTextFiles) {
    $findings.Add($finding)
}

$grouped = $findings | Group-Object Severity
$counts = @{
    error   = 0
    warning = 0
    info    = 0
}
foreach ($group in $grouped) {
    $counts[$group.Name] = $group.Count
}

$report = New-Object System.Collections.Generic.List[string]
$report.Add("# FPDS Cleanup Audit")
$report.Add("")
$report.Add("Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz")")
$report.Add("")
$report.Add("Summary:")
$report.Add("- Errors: $($counts.error)")
$report.Add("- Warnings: $($counts.warning)")
$report.Add("- Info: $($counts.info)")
$report.Add("")

if ($findings.Count -eq 0) {
    $report.Add("No findings.")
}
else {
    foreach ($severity in @("error", "warning", "info")) {
        $section = @($findings | Where-Object { $_.Severity -eq $severity })
        if ($section.Count -eq 0) {
            continue
        }

        $report.Add("## $($severity.Substring(0,1).ToUpper() + $severity.Substring(1))")
        $report.Add("")
        foreach ($finding in $section) {
            $report.Add([string]::Format("- `{0}`: {1}", $finding.File, $finding.Message))
        }
        $report.Add("")
    }
}

$reportText = [string]::Join([Environment]::NewLine, $report)

if ($ReportPath) {
    $absoluteReportPath = [System.IO.Path]::GetFullPath((Join-Path (Get-RepoRoot) $ReportPath))
    $directory = Split-Path -Parent $absoluteReportPath
    if ($directory -and -not (Test-Path -LiteralPath $directory)) {
        New-Item -ItemType Directory -Path $directory | Out-Null
    }
    [System.IO.File]::WriteAllText($absoluteReportPath, $reportText + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))
}

if ($env:GITHUB_STEP_SUMMARY) {
    Add-Content -LiteralPath $env:GITHUB_STEP_SUMMARY -Value $reportText
}

Write-Host $reportText
exit 0
