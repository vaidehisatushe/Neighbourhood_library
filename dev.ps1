#!/usr/bin/env pwsh
#Requires -Version 5.1
<#
.SYNOPSIS
    Neighbourhood Library - Automated Development Environment Control Script
    
.DESCRIPTION
    Fully automated PowerShell script to manage the entire Neighbourhood Library application stack.
    Handles Docker setup, image building, container orchestration, and service verification.
    
.PARAMETER Action
    Action to perform: 'run' (start all services), 'stop' (graceful shutdown), 'exit' (stop and cleanup)
    
.EXAMPLE
    .\dev.ps1 run      # Start the entire stack
    .\dev.ps1 stop     # Stop services gracefully
    .\dev.ps1 exit     # Stop, cleanup, and exit
#>

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("run", "stop", "exit", "dry-run")]
    [string]$Action = "run"
)

# Script configuration
$ErrorActionPreference = "Stop"
$WarningPreference = "SilentlyContinue"
$RepoRoot = (Get-Item $PSScriptRoot).FullName
$DockerComposePath = Join-Path $RepoRoot "docker-compose.yml"
$FrontendPort = 3000
$GatewayPort = 8080
$GatewayHealthPort = 8081

# Color output helpers
function Write-Header {
    param([string]$Message)
    Write-Host "`n" -NoNewline
    Write-Host "=" * 70 -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Cyan -NoNewline
    Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host ("[OK] " + $Message) -ForegroundColor Green
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host ("[ERROR] " + $Message) -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host ("[INFO] " + $Message) -ForegroundColor Yellow
}

# Check prerequisites
function Test-Prerequisites {
    Write-Header "Checking Prerequisites"
    
    try {
        $DockerVersion = docker --version 2>$null
        Write-Success "Docker found: $DockerVersion"
    } catch {
        Write-Error-Custom "Docker not found or not running. Please install Docker Desktop and ensure it is running."
        exit 1
    }
    
    try {
        $ComposeVersion = docker compose version 2>$null
        Write-Success "Docker Compose found: $ComposeVersion"
    } catch {
        Write-Error-Custom "Docker Compose not found."
        exit 1
    }
    
    if (-not (Test-Path $DockerComposePath)) {
        Write-Error-Custom "docker-compose.yml not found at $DockerComposePath"
        exit 1
    }
    Write-Success "docker-compose.yml found"
}

# Check if Neighbourhood_library resources already exist
function Test-ExistingResources {
    Write-Header "Checking for Existing Resources"
    
    $ImageExists = $false
    $ContainerExists = $false
    
    try {
        $output = @(docker images --filter "reference=*neighbourhood*" -q 2>$null)
        if ($output.Count -gt 0) {
            $ImageExists = $true
        }
    } catch {
        # Silently ignore
    }
    
    try {
        $output = @(docker ps -aq --filter "name=neighbourhood" 2>$null)
        if ($output.Count -gt 0) {
            $ContainerExists = $true
        }
    } catch {
        # Silently ignore
    }
    
    if ($ImageExists -or $ContainerExists) {
        Write-Error-Custom "Neighbourhood Library resources already exist!"
        Write-Host ""
        
        if ($ImageExists) {
            Write-Host "Existing images:" -ForegroundColor Yellow
            docker images --filter "reference=*neighbourhood*" --format "{{.Repository}}:{{.Tag}}" 2>$null | ForEach-Object { Write-Host "  - $_" }
        }
        
        if ($ContainerExists) {
            Write-Host "Existing containers:" -ForegroundColor Yellow
            docker ps -a --filter "name=neighbourhood" --format "{{.Names}}" 2>$null | ForEach-Object { Write-Host "  - $_" }
        }
        
        Write-Host ""
        Write-Info "To remove existing resources, run: .\dev.ps1 exit"
        Write-Info "Then run: .\dev.ps1 run again"
        exit 1
    }
    
    Write-Success "No existing Neighbourhood Library resources found"
}

# Build Docker images
function Build-Images {
    Write-Header "Building Docker Images"
    Write-Info "This may take a few minutes on first run..."
    
    Set-Location $RepoRoot
    $ErrorActionPreference = "Continue"
    docker compose build 2>&1 | Out-Null
    $ErrorActionPreference = "Stop"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error-Custom "Docker build failed. Check logs above."
        exit 1
    }
    
    Write-Success "Docker images built successfully"
}

# Start services
function Start-Services {
    Write-Header "Starting Services"
    
    Set-Location $RepoRoot
    #docker compose up -d 2>&1

    $ErrorActionPreference = "Continue"
    docker compose up -d  2>&1 | Out-Null
    $ErrorActionPreference = "Stop"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error-Custom "Failed to start services."
        exit 1
    }
    
    Write-Success "Services started in detached mode"
}

# Wait for services to be ready
function Wait-ForServices {
    Write-Header "Waiting for Services to Be Ready"
    
    $MaxRetries = 30
    $RetryCount = 0
    $HealthCheckPassed = $false
    
    while ($RetryCount -lt $MaxRetries) {
        $RetryCount++
        Write-Info "Health check attempt $RetryCount/$MaxRetries..."
        
        try {
            $Containers = docker ps --format json 2>$null | ConvertFrom-Json -ErrorAction SilentlyContinue
            $TotalCount = (docker compose ps --services 2>$null | Measure-Object -Line).Lines
            
            if ($Containers) {
                $RunningCount = @($Containers).Count
            } else {
                $RunningCount = 0
            }
            
            # Check if all expected services are running
            if ($RunningCount -ge $TotalCount) {
                Write-Success "All services are running!"
                $HealthCheckPassed = $true
                break
            }
            
            Write-Info "Containers running: $RunningCount/$TotalCount"
        } catch {
            Write-Info "Waiting for services..."
        }
        
        Start-Sleep -Seconds 2
    }
    
    if (-not $HealthCheckPassed) {
        Write-Error-Custom "Services did not start within timeout period"
        Write-Info "Checking logs with: docker compose logs"
        docker compose logs 2>$null
        exit 1
    }
}

# Display access URLs
function Show-AccessUrls {
    Write-Header "Access Urls"
    
    $FrontendUrl = "http://localhost:$FrontendPort"
    $GatewayUrl = "http://localhost:$GatewayPort"
    
    Write-Host ""
    Write-Host "Frontend:         $FrontendUrl" -ForegroundColor Cyan
    Write-Host "Gateway API:      $GatewayUrl" -ForegroundColor Cyan
    Write-Host ""
    Write-Info "Open $FrontendUrl in your browser to access the application"
    Write-Host ""
}

# Display logs
function Show-Logs {
    Write-Header "Live Logs (Press Ctrl+C to stop logging, then type 'stop' or 'exit')"
    
    Write-Info "Displaying frontend logs. Additional services available via 'docker compose logs <service>'"
    Write-Host ""
    
    try {
        docker compose logs frontend --follow --timestamps 2>$null
    } catch {
        # Ctrl+C was pressed
        Write-Host ""
    }
}

# Display next steps
function Show-NextSteps {
    Write-Header "Next Steps"
    
    Write-Host ""
    Write-Host "1. Open your browser and navigate to: http://localhost:3000" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "2. Available commands while running:" -ForegroundColor Cyan
    Write-Host "   View all service logs:     docker compose logs --follow" -ForegroundColor Yellow
    Write-Host "   View specific service:     docker compose logs <service> --follow" -ForegroundColor Yellow
    Write-Host "   Execute into container:    docker compose exec <service> sh" -ForegroundColor Yellow
    Write-Host "   Run tests:                 docker compose exec server pytest -q" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "3. To stop the application, press Ctrl+C in this window and type 'stop' or 'exit'" -ForegroundColor Cyan
    Write-Host ""
}

# Stop services
function Stop-Services {
    Write-Header "Stopping Services"
    
    Set-Location $RepoRoot
    #docker compose stop 2>&1 | Out-Null

    $ErrorActionPreference = "Continue"
    docker compose stop 2>&1 | Out-Null
    $ErrorActionPreference = "Stop"
    
    Write-Success "Services stopped gracefully"
}

# Cleanup resources
function Cleanup-Resources {
    Write-Header "Cleaning Up Resources"
    
    Set-Location $RepoRoot
    
    Write-Info "Removing docker compose resources..."
    docker compose down -v --remove-orphans 2>&1 | Out-Null
    
    Write-Info "Forcefully removing Neighbourhood_library containers..."
    docker ps -aq --filter "name=neighbourhood" 2>&1 | ForEach-Object { docker rm -f $_ 2>&1 | Out-Null }
    
    Write-Info "Forcefully removing Neighbourhood_library images..."
    docker images --filter "reference=*neighbourhood*" -q 2>&1 | ForEach-Object { docker rmi -f $_ 2>&1 | Out-Null }
    
    Write-Info "Removing dangling images..."
    docker image prune -f 2>&1 | Out-Null
    
    Write-Info "Removing dangling volumes..."
    docker volume prune -f 2>&1 | Out-Null
    
    Write-Success "All Neighbourhood_library resources and dangling artifacts removed"
}

# Dry-run: list resources that would be removed without deleting
function Show-DryRun {
    Write-Header "Dry-run: Resources that would be removed"

    Set-Location $RepoRoot

    Write-Host "\nContainers matching 'neighbourhood':" -ForegroundColor Yellow
    try {
        $containers = docker ps -a --filter "name=neighbourhood" --format "{{.Names}}\t{{.Status}}" 2>$null
        if ($containers) { $containers | ForEach-Object { Write-Host "  - $_" } } else { Write-Host "  (none)" }
    } catch { Write-Host "  (error querying containers)" }

    Write-Host "\nImages matching 'neighbourhood':" -ForegroundColor Yellow
    try {
        $images = docker images --filter "reference=*neighbourhood*" --format "{{.Repository}}:{{.Tag}}" 2>$null
        if ($images) { $images | ForEach-Object { Write-Host "  - $_" } } else { Write-Host "  (none)" }
    } catch { Write-Host "  (error querying images)" }

    Write-Host "\nDangling images (would be pruned):" -ForegroundColor Yellow
    try {
        $dangling = docker images -f "dangling=true" --format "{{.ID}} {{.Repository}}:{{.Tag}}" 2>$null
        if ($dangling) { $dangling | ForEach-Object { Write-Host "  - $_" } } else { Write-Host "  (none)" }
    } catch { Write-Host "  (error querying dangling images)" }

    Write-Host "\nDangling volumes (would be pruned):" -ForegroundColor Yellow
    try {
        $vols = docker volume ls -f "dangling=true" --format "{{.Name}}" 2>$null
        if ($vols) { $vols | ForEach-Object { Write-Host "  - $_" } } else { Write-Host "  (none)" }
    } catch { Write-Host "  (error querying volumes)" }

    Write-Host "\nNo destructive actions were performed (dry-run)." -ForegroundColor Cyan
}

# Main execution
function Main {
    Clear-Host
    
    switch ($Action.ToLower()) {
        "run" {
            Write-Header "Neighbourhood Library - Development Environment"
            
            Test-Prerequisites
            Test-ExistingResources
            Build-Images
            Start-Services
            Wait-ForServices
            Show-AccessUrls
            Show-NextSteps
            Show-Logs
            
            Write-Header "What would you like to do?"
            Write-Host "  1. stop  - Stop services gracefully" -ForegroundColor Yellow
            Write-Host "  2. exit  - Stop and cleanup everything" -ForegroundColor Yellow
            Write-Host "  3. run   - (Ctrl+C to stop logs, then restart)" -ForegroundColor Yellow
            Write-Host ""
            $NextAction = Read-Host "Enter command (stop/exit)"
            
            if ($NextAction -eq "stop") {
                Stop-Services
            } elseif ($NextAction -eq "exit") {
                Stop-Services
                Cleanup-Resources
            } else {
                Write-Info "Unknown command. Exiting gracefully."
            }
        }
        
        "stop" {
            Stop-Services
            Write-Info "Services stopped. Containers remain but are not running."
            Write-Info "Run '.\dev.ps1 run' to restart, or '.\dev.ps1 exit' to cleanup."
        }
        
        "dry-run" {
            Show-DryRun
        }
        
        "exit" {
            Write-Header "Neighbourhood Library - Full Cleanup"
            Stop-Services
            Cleanup-Resources
            Write-Success "Application fully stopped and cleaned up"
        }
        
        default {
            Write-Error-Custom "Unknown action: $Action"
            Write-Host "Usage: .\dev.ps1 [run|stop|exit|dry-run]" -ForegroundColor Yellow
            exit 1
        }
    }
}

# Run main
Main
