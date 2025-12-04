# dev.ps1 - Automated Development Environment Script

A comprehensive PowerShell script to fully automate the Neighbourhood Library application stack (Docker Compose) with a single command.

## Features
- ✓ Automatic Docker prerequisite checks
- ✓ Builds all Docker images (server, gateway, frontend, db)
- ✓ Starts all services in detached mode
- ✓ Health checks with retry logic
- ✓ Displays application access URLs
- ✓ Live service logs with follow mode
- ✓ Interactive stop/exit/restart commands
- ✓ Graceful shutdown and cleanup

## Quick Start

### First Run
```powershell
cd C:\workspace\Neighbourhood_library
.\dev.ps1 run
```

This will:
1. ✓ Check Docker and Docker Compose are installed
2. ✓ Build all Docker images
3. ✓ Start all containers (db, server, gateway, frontend)
4. ✓ Wait for services to be healthy
5. ✓ Display the frontend URL: **http://localhost:3000**
6. ✓ Show live logs
7. ✓ Prompt for next action (stop/exit)

### Control Commands

**Start the application:**
```powershell
.\dev.ps1 run
```

**Stop services (keep containers):**
```powershell
.\dev.ps1 stop
```

**Stop and cleanup everything (volumes, containers):**
```powershell
.\dev.ps1 exit
```

## Interactive Mode

After the application starts and logs are displayed, you can:
- **Ctrl+C** to stop viewing logs
- Type **stop** to gracefully stop all services
- Type **exit** to stop and remove all containers/volumes

## What Gets Started

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000 | React UI |
| Gateway | http://localhost:8080 | Node.js API Gateway |
| Server | gRPC on 50051 | Python gRPC Backend |
| Database | localhost:5432 | PostgreSQL 15 |

## Troubleshooting

**Docker not running:**
```
Start Docker Desktop and ensure WSL2 backend is enabled
```

**Port already in use:**
```powershell
# Find process using port
netstat -ano | findstr :3000
# Kill process (replace PID)
taskkill /PID <PID> /F
```

**Check detailed logs:**
```powershell
# After starting with .\dev.ps1 run, in another terminal:
docker compose logs -f
```

**Rebuild from scratch:**
```powershell
.\dev.ps1 exit
.\dev.ps1 run
```

## Manual Docker Commands (if needed)

```powershell
# View all running containers
docker compose ps

# View logs for a specific service
docker compose logs <service> -f

# Execute command in a container
docker compose exec <service> sh

# Run tests
docker compose exec server pytest -q
```

## Script Behavior

- **run**: Builds, starts, health-checks, and shows logs
- **stop**: Graceful shutdown (services stop but volumes persist)
- **exit**: Full cleanup (stops services + removes containers/volumes)

## Requirements

- Windows 10/11 with PowerShell 5.1+
- Docker Desktop with WSL2 backend enabled
- ~5-10 GB disk space for Docker images and volumes
