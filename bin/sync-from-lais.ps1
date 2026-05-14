#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Sync key configurations from main LAIS to LAIS-agent-CoComm
.DESCRIPTION
    Copies agent registry, MCP configs, and protocol settings from the
    main LAIS system into the CoComm standalone package.
.PARAMETER Source
    Path to main LAIS system (default: $env:LAIS_HOME or parent of this repo)
.PARAMETER Target
    Path to LAIS-agent-CoComm repo (default: this script's parent)
.EXAMPLE
    ./sync-from-lais.ps1
#>

param(
    [string]$Source,
    [string]$Target = Split-Path $PSScriptRoot -Parent
)

# Auto-detect source if not provided
if (-not $Source) {
    $projectRoot = Split-Path (Split-Path $Target -Parent) -Parent
    $Source = Join-Path $projectRoot "models/ai_engine"
}

if (-not (Test-Path $Source)) {
    Write-Error "Source path not found: $Source"
    exit 1
}

Write-Host "=== LAIS to CoComm Sync ===" -ForegroundColor Cyan
Write-Host "Source: $Source"
Write-Host "Target: $Target"

# Files to sync (source -> target relative path)
$syncMap = @(
    @{
        Source = "knowledge/memory/agent_registry.json"
        Target = "config/agent_registry.json"
        Desc = "Agent registry"
    },
    @{
        Source = "knowledge/memory/mcp_config.json"
        Target = "config/mcp_config.json"
        Desc = "MCP server configuration"
    },
    @{
        Source = "knowledge/memory/a2a_config.json"
        Target = "config/a2a_config.json"
        Desc = "A2A agent configuration"
    },
    @{
        Source = "unified_layer/protocol_layer.py"
        Target = "src/agent_sync/_protocol_layer_main.py"
        Desc = "Full protocol layer (reference)"
    }
)

$syncCount = 0

foreach ($item in $syncMap) {
    $srcPath = Join-Path $Source $item.Source
    $tgtPath = Join-Path $Target $item.Target

    if (Test-Path $srcPath) {
        # Create target directory if needed
        $tgtDir = Split-Path $tgtPath -Parent
        if (-not (Test-Path $tgtDir)) {
            New-Item -ItemType Directory -Path $tgtDir -Force | Out-Null
        }

        # Copy file
        Copy-Item $srcPath $tgtPath -Force
        Write-Host "[SYNC] $($item.Desc)" -ForegroundColor Green
        $syncCount++
    } else {
        Write-Host "[SKIP] $($item.Desc) (not found: $srcPath)" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Synced $syncCount files" -ForegroundColor $(if ($syncCount -gt 0) { "Green" } else { "Yellow" })

# Generate agent list for CoComm
$registryPath = Join-Path $Source "knowledge/memory/agent_registry.json"
if (Test-Path $registryPath) {
    $registry = Get-Content $registryPath -Raw | ConvertFrom-Json
    Write-Host ""
    Write-Host "Registered agents:" -ForegroundColor Cyan
    foreach ($agent in $registry) {
        Write-Host "  - $($agent.agent_id): $($agent.capabilities -join ', ')"
    }
}

Write-Host ""
Write-Host "Done. Review changes with 'git status' in CoComm folder." -ForegroundColor Gray