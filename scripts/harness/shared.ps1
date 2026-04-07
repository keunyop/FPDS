Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-RepoRoot {
    $root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
    return $root.Path
}

function Get-StagedFiles {
    Push-Location (Get-RepoRoot)
    try {
        $output = & git diff --cached --name-only --diff-filter=ACMR
        if (-not $output) {
            return @()
        }

        return @($output | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
    }
    finally {
        Pop-Location
    }
}

function Test-TextFilePath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RelativePath
    )

    $extensions = @(
        ".md", ".txt", ".json", ".yml", ".yaml", ".js", ".jsx", ".ts", ".tsx",
        ".mjs", ".cjs", ".css", ".scss", ".html", ".ps1", ".sh", ".env", ".gitignore"
    )

    foreach ($extension in $extensions) {
        if ($RelativePath.EndsWith($extension, [System.StringComparison]::OrdinalIgnoreCase)) {
            return $true
        }
    }

    return $false
}

function Get-AbsolutePath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RelativePath
    )

    return [System.IO.Path]::GetFullPath((Join-Path (Get-RepoRoot) $RelativePath))
}

function Get-RepoRelativePath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$AbsolutePath
    )

    $root = (Get-RepoRoot).TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
    $rootUri = [System.Uri]::new($root)
    $fileUri = [System.Uri]::new($AbsolutePath)
    $relativeUri = $rootUri.MakeRelativeUri($fileUri)
    $relativePath = [System.Uri]::UnescapeDataString($relativeUri.ToString())
    return $relativePath.Replace('/', [System.IO.Path]::DirectorySeparatorChar)
}

function Normalize-TextContent {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Content
    )

    $normalized = $Content -replace "`r`n", "`n"
    $normalized = $normalized -replace "`r", "`n"
    $lines = $normalized -split "`n", -1

    for ($index = 0; $index -lt $lines.Count; $index++) {
        $lines[$index] = $lines[$index] -replace "[ \t]+$", ""
    }

    $result = [string]::Join("`n", $lines)

    if (-not $result.EndsWith("`n")) {
        $result += "`n"
    }

    return $result
}

function Invoke-TextAutoFix {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RelativePath
    )

    $absolutePath = Get-AbsolutePath -RelativePath $RelativePath
    if (-not (Test-Path -LiteralPath $absolutePath)) {
        return $false
    }

    $original = [System.IO.File]::ReadAllText($absolutePath)
    $updated = Normalize-TextContent -Content $original

    if ($original -ceq $updated) {
        return $false
    }

    [System.IO.File]::WriteAllText($absolutePath, $updated, [System.Text.UTF8Encoding]::new($false))

    Push-Location (Get-RepoRoot)
    try {
        & git add -- $RelativePath | Out-Null
    }
    finally {
        Pop-Location
    }

    return $true
}

function New-Finding {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Severity,
        [Parameter(Mandatory = $true)]
        [string]$File,
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    return [pscustomobject]@{
        Severity = $Severity
        File     = $File
        Message  = $Message
    }
}

function Resolve-LocalReference {
    param(
        [Parameter(Mandatory = $true)]
        [string]$SourcePath,
        [Parameter(Mandatory = $true)]
        [string]$Reference
    )

    $referencePath = ($Reference -split "[#?]", 2)[0].Trim()
    if ([string]::IsNullOrWhiteSpace($referencePath)) {
        return $null
    }

    if (
        $referencePath.StartsWith("http://") -or
        $referencePath.StartsWith("https://") -or
        $referencePath.StartsWith("mailto:") -or
        $referencePath.StartsWith("app://") -or
        $referencePath.StartsWith("plugin://")
    ) {
        return $null
    }

    try {
        if ($referencePath.StartsWith("/")) {
            return [System.IO.Path]::GetFullPath((Join-Path (Get-RepoRoot) $referencePath.TrimStart('/', '\')))
        }

        $rootAnchors = @("docs/", "docs\", "scripts/", "scripts\", ".github/", ".github\", ".githooks/", ".githooks\", "README.md", "AGENTS.md")
        foreach ($anchor in $rootAnchors) {
            if ($referencePath.StartsWith($anchor, [System.StringComparison]::OrdinalIgnoreCase)) {
                return [System.IO.Path]::GetFullPath((Join-Path (Get-RepoRoot) $referencePath))
            }
        }

        $sourceDirectory = Split-Path -Parent (Get-AbsolutePath -RelativePath $SourcePath)
        return [System.IO.Path]::GetFullPath((Join-Path $sourceDirectory $referencePath))
    }
    catch {
        return $null
    }
}

function Test-LocalFileReferenceShape {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Reference
    )

    if ([string]::IsNullOrWhiteSpace($Reference)) {
        return $false
    }

    $referencePath = ($Reference -split "[#?]", 2)[0].Trim()
    if ([string]::IsNullOrWhiteSpace($referencePath)) {
        return $false
    }

    if ($referencePath -match '^(docs|scripts|\.github|\.githooks)[\\/].+\.[A-Za-z0-9]{1,8}$') {
        return $true
    }

    if ($referencePath -match '^(README|AGENTS)\.md$') {
        return $true
    }

    if ($referencePath -match '^(\.?\.?[\\/]).+\.[A-Za-z0-9]{1,8}$') {
        return $true
    }

    return $false
}

function Get-MarkdownReferenceFindings {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$RelativePaths
    )

    $findings = [System.Collections.Generic.List[object]]::new()

    foreach ($relativePath in $RelativePaths) {
        $absolutePath = Get-AbsolutePath -RelativePath $relativePath
        if (-not (Test-Path -LiteralPath $absolutePath)) {
            continue
        }

        $content = [System.IO.File]::ReadAllText($absolutePath)
        $markdownLinks = [System.Text.RegularExpressions.Regex]::Matches($content, '\[[^\]]+\]\(([^)]+)\)')
        foreach ($match in $markdownLinks) {
            $reference = $match.Groups[1].Value.Trim()
            $resolved = Resolve-LocalReference -SourcePath $relativePath -Reference $reference
            if ($null -ne $resolved -and -not (Test-Path -LiteralPath $resolved)) {
                $findings.Add((New-Finding -Severity "error" -File $relativePath -Message "Broken Markdown link: $reference"))
            }
        }

        $inlineRefs = [System.Text.RegularExpressions.Regex]::Matches($content, '`([^`]+)`')
        foreach ($match in $inlineRefs) {
            $reference = $match.Groups[1].Value.Trim()
            if ([string]::IsNullOrWhiteSpace($reference)) {
                continue
            }
            if (-not (Test-LocalFileReferenceShape -Reference $reference)) {
                continue
            }

            $resolved = Resolve-LocalReference -SourcePath $relativePath -Reference $reference
            if ($null -ne $resolved -and -not (Test-Path -LiteralPath $resolved)) {
                $findings.Add((New-Finding -Severity "error" -File $relativePath -Message "Broken inline file reference: $reference"))
            }
        }
    }

    return $findings.ToArray()
}

function Get-PowerShellSyntaxFindings {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$RelativePaths
    )

    $findings = [System.Collections.Generic.List[object]]::new()

    foreach ($relativePath in $RelativePaths) {
        $absolutePath = Get-AbsolutePath -RelativePath $relativePath
        if (-not (Test-Path -LiteralPath $absolutePath)) {
            continue
        }

        $tokens = $null
        $errors = $null
        [System.Management.Automation.Language.Parser]::ParseFile($absolutePath, [ref]$tokens, [ref]$errors) | Out-Null

        foreach ($error in $errors) {
            $message = "{0} (line {1})" -f $error.Message, $error.Extent.StartLineNumber
            $findings.Add((New-Finding -Severity "error" -File $relativePath -Message $message))
        }
    }

    return $findings.ToArray()
}

function Get-TrailingWhitespaceFindings {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$RelativePaths
    )

    $findings = [System.Collections.Generic.List[object]]::new()

    foreach ($relativePath in $RelativePaths) {
        if ($relativePath.StartsWith("scripts\harness\", [System.StringComparison]::OrdinalIgnoreCase)) {
            continue
        }

        if (-not (Test-TextFilePath -RelativePath $relativePath)) {
            continue
        }

        $absolutePath = Get-AbsolutePath -RelativePath $relativePath
        if (-not (Test-Path -LiteralPath $absolutePath)) {
            continue
        }

        $lineNumber = 0
        foreach ($line in [System.IO.File]::ReadLines($absolutePath)) {
            $lineNumber++
            $isMarkdownLineBreak = $relativePath.EndsWith(".md", [System.StringComparison]::OrdinalIgnoreCase) -and $line -match " {2}$" -and $line -notmatch " {3,}$"
            if ($isMarkdownLineBreak) {
                continue
            }

            if ($line -match "[ \t]+$") {
                $findings.Add((New-Finding -Severity "warning" -File $relativePath -Message "Trailing whitespace at line $lineNumber"))
            }
        }
    }

    return $findings.ToArray()
}

function Get-TextFilesUnderRepo {
    $root = Get-RepoRoot
    $files = Get-ChildItem -Path $root -Recurse -File | Where-Object {
        $_.FullName -notmatch "\\\.git\\"
    }

    $relativePaths = foreach ($file in $files) {
        $relativePath = Get-RepoRelativePath -AbsolutePath $file.FullName
        if (Test-TextFilePath -RelativePath $relativePath) {
            $relativePath
        }
    }

    return @($relativePaths)
}

function Get-MarkdownFilesUnderRepo {
    $root = Get-RepoRoot
    $files = Get-ChildItem -Path $root -Recurse -Filter *.md -File | Where-Object {
        $_.FullName -notmatch "\\\.git\\"
    }

    return @($files | ForEach-Object { Get-RepoRelativePath -AbsolutePath $_.FullName })
}

function Get-PowerShellFilesUnderRepo {
    $root = Get-RepoRoot
    $files = Get-ChildItem -Path $root -Recurse -Filter *.ps1 -File | Where-Object {
        $_.FullName -notmatch "\\\.git\\"
    }

    return @($files | ForEach-Object { Get-RepoRelativePath -AbsolutePath $_.FullName })
}

function Get-RequiredHarnessPaths {
    return @(
        "AGENTS.md",
        "README.md",
        "docs/README.md",
        "docs/00-governance/harness-engineering-baseline.md",
        ".githooks/pre-commit",
        "scripts/harness/install-hooks.ps1",
        "scripts/harness/pre-commit.ps1",
        "scripts/harness/repo-doctor.ps1",
        "scripts/harness/cleanup-audit.ps1",
        "scripts/harness/invoke-project-checks.ps1",
        ".github/workflows/harness.yml"
    )
}

function Get-HarnessMissingFileFindings {
    $findings = [System.Collections.Generic.List[object]]::new()

    foreach ($relativePath in Get-RequiredHarnessPaths) {
        $absolutePath = Get-AbsolutePath -RelativePath $relativePath
        if (-not (Test-Path -LiteralPath $absolutePath)) {
            $findings.Add((New-Finding -Severity "error" -File $relativePath -Message "Required harness file is missing"))
        }
    }

    return $findings.ToArray()
}

function Get-TodoFindings {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$RelativePaths
    )

    $findings = [System.Collections.Generic.List[object]]::new()
    $pattern = "\b(TODO|FIXME|HACK)\b"

    foreach ($relativePath in $RelativePaths) {
        if ($relativePath.StartsWith("scripts\harness\", [System.StringComparison]::OrdinalIgnoreCase)) {
            continue
        }

        if (-not (Test-TextFilePath -RelativePath $relativePath)) {
            continue
        }

        $absolutePath = Get-AbsolutePath -RelativePath $relativePath
        if (-not (Test-Path -LiteralPath $absolutePath)) {
            continue
        }

        $lineNumber = 0
        foreach ($line in [System.IO.File]::ReadLines($absolutePath)) {
            $lineNumber++
            if ($line -match "TODO/FIXME/HACK" -or $line -match "TODO-like") {
                continue
            }
            if ($line -match $pattern) {
                $findings.Add((New-Finding -Severity "info" -File $relativePath -Message "TODO-like marker at line $lineNumber"))
            }
        }
    }

    return $findings.ToArray()
}

function Write-Findings {
    param(
        [Parameter(Mandatory = $true)]
        [object[]]$Findings
    )

    foreach ($finding in $Findings) {
        Write-Error ("[{0}] {1}: {2}" -f $finding.Severity.ToUpperInvariant(), $finding.File, $finding.Message)
    }
}
