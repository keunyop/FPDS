[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "shared.ps1")

function Get-EnvMap {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RelativePath
    )

    $absolutePath = Get-AbsolutePath -RelativePath $RelativePath
    $map = @{}

    foreach ($line in [System.IO.File]::ReadLines($absolutePath)) {
        $trimmed = $line.Trim()
        if ([string]::IsNullOrWhiteSpace($trimmed)) {
            continue
        }
        if ($trimmed.StartsWith("#")) {
            continue
        }

        $parts = $trimmed.Split("=", 2)
        if ($parts.Count -ne 2) {
            throw "Invalid env line in ${RelativePath}: $line"
        }

        $key = $parts[0].Trim()
        $value = $parts[1].Trim()

        if ([string]::IsNullOrWhiteSpace($key)) {
            throw "Empty env key in ${RelativePath}: $line"
        }

        if ($map.ContainsKey($key)) {
            throw "Duplicate env key '$key' in $RelativePath"
        }

        $map[$key] = $value
    }

    return $map
}

function Assert-HasKeys {
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$Map,
        [Parameter(Mandatory = $true)]
        [string[]]$Keys,
        [Parameter(Mandatory = $true)]
        [string]$Label
    )

    foreach ($key in $Keys) {
        if (-not $Map.ContainsKey($key)) {
            throw "$Label is missing required key '$key'"
        }
    }
}

$requiredFiles = @(
    "docs/03-design/monitoring-error-tracking-baseline.md",
    "docs/00-governance/foundation-ci-cd-baseline.md",
    "shared/observability/error-envelope.example.json",
    "shared/observability/structured-log-event.example.json",
    ".env.dev.example",
    ".env.prod.example"
)

foreach ($relativePath in $requiredFiles) {
    $absolutePath = Get-AbsolutePath -RelativePath $relativePath
    if (-not (Test-Path -LiteralPath $absolutePath)) {
        throw "Required foundation baseline file is missing: $relativePath"
    }
}

$devEnv = Get-EnvMap -RelativePath ".env.dev.example"
$prodEnv = Get-EnvMap -RelativePath ".env.prod.example"
$requiredObservabilityKeys = @(
    "FPDS_LOG_LEVEL",
    "FPDS_REQUEST_ID_HEADER",
    "FPDS_MONITORING_PROVIDER",
    "FPDS_MONITORING_DSN"
)

Assert-HasKeys -Map $devEnv -Keys $requiredObservabilityKeys -Label ".env.dev.example"
Assert-HasKeys -Map $prodEnv -Keys $requiredObservabilityKeys -Label ".env.prod.example"

$allowedProviders = @("disabled", "sentry", "custom")
if ($allowedProviders -notcontains $devEnv["FPDS_MONITORING_PROVIDER"]) {
    throw ".env.dev.example has unsupported FPDS_MONITORING_PROVIDER '$($devEnv["FPDS_MONITORING_PROVIDER"])'"
}
if ($allowedProviders -notcontains $prodEnv["FPDS_MONITORING_PROVIDER"]) {
    throw ".env.prod.example has unsupported FPDS_MONITORING_PROVIDER '$($prodEnv["FPDS_MONITORING_PROVIDER"])'"
}
if ($prodEnv["FPDS_MONITORING_PROVIDER"] -eq "disabled") {
    throw ".env.prod.example must not keep FPDS_MONITORING_PROVIDER=disabled"
}
if ([string]::IsNullOrWhiteSpace($devEnv["FPDS_REQUEST_ID_HEADER"])) {
    throw ".env.dev.example must define FPDS_REQUEST_ID_HEADER"
}
if ([string]::IsNullOrWhiteSpace($prodEnv["FPDS_REQUEST_ID_HEADER"])) {
    throw ".env.prod.example must define FPDS_REQUEST_ID_HEADER"
}

$errorEnvelope = Get-Content (Get-AbsolutePath -RelativePath "shared/observability/error-envelope.example.json") -Raw | ConvertFrom-Json
if (-not $errorEnvelope.error.code) {
    throw "error-envelope.example.json must define error.code"
}
if (-not $errorEnvelope.error.message) {
    throw "error-envelope.example.json must define error.message"
}
if (-not $errorEnvelope.error.request_id) {
    throw "error-envelope.example.json must define error.request_id"
}

$structuredEvent = Get-Content (Get-AbsolutePath -RelativePath "shared/observability/structured-log-event.example.json") -Raw | ConvertFrom-Json
$requiredEventProperties = @(
    "timestamp",
    "level",
    "environment",
    "runtime_label",
    "surface",
    "component",
    "event_type",
    "request_id",
    "correlation_id",
    "run_id",
    "error_code",
    "message",
    "safe_context",
    "monitoring"
)

foreach ($property in $requiredEventProperties) {
    if (-not ($structuredEvent.PSObject.Properties.Name -contains $property)) {
        throw "structured-log-event.example.json must define '$property'"
    }
}

if (-not ($structuredEvent.monitoring.PSObject.Properties.Name -contains "provider")) {
    throw "structured-log-event.example.json must define monitoring.provider"
}
if (-not ($structuredEvent.monitoring.PSObject.Properties.Name -contains "capture")) {
    throw "structured-log-event.example.json must define monitoring.capture"
}

Write-Host "Foundation baseline validation passed."
