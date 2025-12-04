# DEVELOPMENT.md

## Prerequisites
- Docker Desktop (recommended) or local Python 3.11+, Node.js 18+, npm
- (Optional) `grpcio-tools` for Python: `pip install grpcio-tools`

## Quick Start (Docker, recommended)
```powershell
cd C:\workspace\Neighbourhood_library
docker compose build --progress=plain
docker compose up -d
docker compose ps
```

## Stopping and Cleaning Up
```powershell
docker compose down
```

## Running Tests (in Docker)
```powershell
docker compose exec server pytest -q
```

## Running Tests (locally)
```powershell
cd server
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install pytest
pytest -q
```

## Generating Python gRPC Files for Clients
```powershell
cd server
python -m grpc_tools.protoc -I../protos --python_out=../clients --grpc_python_out=../clients ../protos/library.proto
```

## Running the Frontend Locally
```powershell
cd frontend
npm install
npm run dev
```

## Running the Gateway Locally
```powershell
cd gateway
npm install
node server.js
```

## Running the Server Locally
```powershell
cd server
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

## Troubleshooting
- If you see `ModuleNotFoundError: No module named 'library_pb2'`, run the proto generation step above.
- If Docker Compose can't connect to the daemon, start Docker Desktop and ensure WSL2 backend is enabled.
- For build errors, check that all referenced files exist and build context is correct in `docker-compose.yml`.
