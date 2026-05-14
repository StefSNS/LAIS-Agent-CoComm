#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Sync enhancements from LAIS-agent-CoComm back to main LAIS
.DESCRIPTION
    Copies new modules (MCP Bridge, WebSocket, etc.) from CoComm
    into the main LAIS system for integration.
.PARAMETER Source
    Path to LAIS-agent-CoComm repo (default: this script's parent)
.PARAMETER Target
    Path to main LAIS system (default: $env:LAIS_HOME or parent of source)
.EXAMPLE
    ./sync-to-lais.ps1
#>

param(
    [string]$Source = Split-Path $PSScriptRoot -Parent,
    [string]$Target
)

# Auto-detect target if not provided
if (-not $Target) {
    $projectRoot = Split-Path (Split-Path $Source -Parent) -Parent
    $Target = Join-Path $projectRoot "models/ai_engine"
}

if (-not (Test-Path $Target)) {
    Write-Error "Target path not found: $Target"
    exit 1
}

Write-Host "=== CoComm to LAIS Sync ===" -ForegroundColor Cyan
Write-Host "Source: $Source"
Write-Host "Target: $Target"

# New modules to copy from CoComm to LAIS
$syncMap = @(
    @{
        Source = "src/agent_sync/mcp_bridge.py"
        Target = "unified_layer/mcp_bridge.py"
        Desc = "MCP Bridge"
    },
    @{
        Source = "src/agent_sync/websocket_server.py"
        Target = "unified_layer/websocket_server.py"
        Desc = "WebSocket Server"
    },
    @{
        Source = "src/agent_sync/goal_planner.py"
        Target = "unified_layer/goal_planner.py"
        Desc = "Goal Planner / DAG"
    },
    @{
        Source = "src/agent_sync/consensus.py"
        Target = "unified_layer/consensus.py"
        Desc = "Consensus Engine"
    },
    @{
        Source = "src/agent_sync/graph_evolution.py"
        Target = "unified_layer/graph_evolution.py"
        Desc = "Self-healing Graph"
    }
)

$syncCount = 0

foreach ($item in $syncMap) {
    $srcPath = Join-Path $Source $item.Source
    $tgtPath = Join-Path $Target $item.Target

    if (Test-Path $srcPath) {
        # Backup existing if present
        if (Test-Path $tgtPath) {
            $backup = "$tgtPath.bak"
            Copy-Item $tgtPath $backup -Force
            Write-Host "[BACKUP] $($item.Desc) -> $backup" -ForegroundColor Yellow
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
Write-Host "Synced $syncCount modules" -ForegroundColor $(if ($syncCount -gt 0) { "Green" } else { "Yellow" })

# Update __init__.py in LAIS if it exists
$initPath = Join-Path $Target "unified_layer/__init__.py"
if (Test-Path $initPath) {
    Write-Host ""
    Write-Host "[UPDATE] unified_layer/__init__.py" -ForegroundColor Cyan
    Write-Host "  Add imports for new modules" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Done. Review and test changes in LAIS." -ForegroundColor Gray