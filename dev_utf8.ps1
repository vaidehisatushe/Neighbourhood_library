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
    [ValidateSet("run", "stop", "exit")]
    [string]$Action = "run"
)

# Script configuration
$ErrorActionPreference = "Stop"
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
    Write-Host "âœ“ $Message" -ForegroundColor Green
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "âœ— $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "â„¹ $Message" -ForegroundColor Yellow
}

# Check prerequisites
function Test-Prerequisites {
    Write-Header "Checking Prerequisites"
    
    # Check Docker
    try {
        $DockerVersion = docker --version 2>$null
        Write-Success "Docker found: $DockerVersion"
    } catch {
        Write-Error-Custom "Docker not found or not running. Please install Docker Desktop and ensure it is running."
        exit 1
    }
    
    # Check Docker Compose
    try {
        $ComposeVersion = docker compose version 2>$null
        Write-Success "Docker Compose found: $ComposeVersion"
    } catch {
        Write-Error-Custom "Docker Compose not found."
        exit 1
    }
    
    # Check docker-compose.yml exists
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
    
    # Check for images with Neighbourhood_library prefix
    try {
        $images = & docker images --filter "reference=*neighbourhood*" -q 2>&1
        if ($images -and $images.Trim().Length -gt 0) {
            $ImageExists = $true
        }
    } catch {
        # Silently handle any errors
    }
    
    # Check for containers with Neighbourhood_library prefix
    try {
        $containers = & docker ps -aq --filter "name=neighbourhood" 2>&1
        if ($containers -and $containers.Trim().Length -gt 0) {
            $ContainerExists = $true
        }
    } catch {
        # Silently handle any errors
    }
    
    if ($ImageExists -or $ContainerExists) {
        Write-Error-Custom "Neighbourhood Library resources already exist!"
        Write-Host ""
        
        if ($ImageExists) {
            Write-Host "Existing images:" -ForegroundColor Yellow
            try {
                $images = & docker images --filter "reference=*neighbourhood*" --format "{{.Repository}}:{{.Tag}}"
                $images | ForEach-Object { Write-Host "  - $_" }
            } catch { }
        }
        
        if ($ContainerExists) {
            Write-Host "Existing containers:" -ForegroundColor Yellow
            try {
                $containers = & docker ps -a --filter "name=neighbourhood" --format "{{.Names}}"
                $containers | ForEach-Object { Write-Host "  - $_" }
            } catch { }
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
    & docker compose build --progress=plain 2>&1 | Tee-Object -FilePath $null
    
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
    & docker compose up -d 2>&1 | Tee-Object -FilePath $null
    
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
        
        # Check if all containers are running
        $Containers = & docker ps --format json 2>$null | ConvertFrom-Json -ErrorAction SilentlyContinue
        $TotalCount = (& docker compose ps --services | Measure-Object).Count
        
        if ($Containers) {
            $RunningCount = ($Containers | Measure-Object).Count
        } else {
            $RunningCount = 0
        }
        
        if ($RunningCount -ge $TotalCount) {
            # Try gateway health check
            try {
                $HealthResponse = Invoke-WebRequest -Uri "http://localhost:$GatewayHealthPort/health" -ErrorAction SilentlyContinue
                if ($HealthResponse.StatusCode -eq 200) {
                    Write-Success "All services are healthy!"
                    $HealthCheckPassed = $true
                    break
                }
            } catch {
                # Not ready yet
            }
        }
        
        Write-Info "Containers running: $RunningCount/$TotalCount"
        Start-Sleep -Seconds 2
    }
    
    if (-not $HealthCheckPassed) {
        Write-Error-Custom "Services did not become healthy within timeout period"
        Write-Info "Checking logs with: docker compose logs"
        & docker compose logs
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

# Display logs (follow mode with exit prompt)
function Show-Logs {
    Write-Header "Live Logs (Press Ctrl+C to stop logging, then type 'stop' or 'exit')"
    
    Write-Info "Displaying frontend logs. Additional services available via 'docker compose logs <service>'"
    Write-Host ""
    
    try {
        & docker compose logs frontend --follow --timestamps
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

# Stop services gracefully (Neighbourhood_library containers)
function Stop-Services {
    Write-Header "Stopping Services"
    
    Set-Location $RepoRoot
    
    Write-Info "Stopping all Neighbourhood_library containers..."
    
    # Try docker compose stop first
    try {
        & docker compose stop 2>&1 | Out-Null
    } catch {
        # Silently handle any errors
    }
    
    # Force stop any remaining containers with neighbourhood prefix
    try {
        $containers = & docker ps -aq --filter "name=neighbourhood" 2>&1
        if ($containers -and $containers.Trim().Length -gt 0) {
            $containers | ForEach-Object {
                if ($_.Trim().Length -gt 0) {
                    & docker stop $_ 2>&1 | Out-Null
                }
            }
        }
    } catch {
        # Silently handle any errors
    }
    
    Write-Success "Services stopped gracefully"
}

# Cleanup and remove volumes, forcefully remove dangling resources
function Cleanup-Resources {
    Write-Header "Cleaning Up Resources"
    
    Set-Location $RepoRoot
    
    # Stop and remove containers/volumes via docker compose
    Write-Info "Removing docker compose resources..."
    try {
        & docker compose down -v --remove-orphans 2>&1 | Out-Null
    } catch {
        # Silently handle any errors
    }
    
    # Force remove all Neighbourhood_library containers
    Write-Info "Forcefully removing Neighbourhood_library containers..."
    try {
        $containers = & docker ps -aq --filter "name=neighbourhood" 2>&1
        if ($containers -and $containers.Trim().Length -gt 0) {
            $containers | ForEach-Object {
                if ($_.Trim().Length -gt 0) {
                    & docker rm -f $_ 2>&1 | Out-Null
                }
            }
        }
    } catch {
        # Silently handle any errors
    }
    
    # Force remove all Neighbourhood_library images
    Write-Info "Forcefully removing Neighbourhood_library images..."
    try {
        $images = & docker images --filter "reference=*neighbourhood*" -q 2>&1
        if ($images -and $images.Trim().Length -gt 0) {
            $images | ForEach-Object {
                if ($_.Trim().Length -gt 0) {
                    & docker rmi -f $_ 2>&1 | Out-Null
                }
            }
        }
    } catch {
        # Silently handle any errors
    }
    
    # Remove dangling images
    Write-Info "Removing dangling images..."
    try {
        & docker image prune -f 2>&1 | Out-Null
    } catch {
        # Silently handle any errors
    }
    
    # Remove dangling volumes
    Write-Info "Removing dangling volumes..."
    try {
        & docker volume prune -f 2>&1 | Out-Null
    } catch {
        # Silently handle any errors
    }
    
    Write-Success "All Neighbourhood_library resources and dangling artifacts removed"
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
            
            # After logs are exited, prompt for next action
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
        
        "exit" {
            Write-Header "Neighbourhood Library - Full Cleanup"
            Stop-Services
            Cleanup-Resources
            Write-Success "Application fully stopped and cleaned up"
        }
        
        default {
            Write-Error-Custom "Unknown action: $Action"
            Write-Host "Usage: .\dev.ps1 [run|stop|exit]" -ForegroundColor Yellow
            exit 1
        }
    }
}

# Run main function
Main
