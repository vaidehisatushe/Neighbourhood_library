# Neighborhood Library Service (zipped deliverable)

This archive contains a working Python gRPC server, protobuf definition, Postgres schema,
a Node.js gateway (REST -> gRPC), a minimal frontend scaffold, and a sample Python client.

## Quick setup

1. Install Docker & Docker Compose.
2. Start Postgres with schema initialization:
   ```bash
   docker-compose up -d
   ```
3. Generate Python protobuf code:
   ```bash
   cd server
   ./generate_protos.sh
   ```
4. Install server deps and run the gRPC server:
   ```bash
   pip install -r server/requirements.txt
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/library GRPC_PORT=50051 python server/app.py
   ```
5. Start the gateway:
   ```bash
   cd gateway
   npm install
   node server.js
   ```
6. Run the sample client:
   ```bash
   python clients/sample_client.py
   ```

## Notes
- Each method in server/app.py has comments/docstrings explaining its exact task.
- You must run the protobuf generation step before running the Python server.
- Frontend is a minimal scaffold; adapt with CRA/Vite if you want a full UI.
