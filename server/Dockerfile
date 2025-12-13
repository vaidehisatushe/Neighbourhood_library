FROM python:3.11-slim
WORKDIR /app
# Install build deps for grpcio-tools and psycopg2
RUN apt-get update && apt-get install -y build-essential python3-dev gcc libpq-dev postgresql-client curl vim && rm -rf /var/lib/apt/lists/*
COPY server/requirements.txt ./
# Install grpcio-tools so we can generate code at build time
RUN pip install --no-cache-dir grpcio-tools
RUN pip install --no-cache-dir -r requirements.txt
COPY server/ .
COPY protos/ ../protos/
# Generate protobuf python files at build time
RUN python -m grpc_tools.protoc -I../protos --python_out=. --grpc_python_out=. ../protos/library.proto || true
ENV DATABASE_URL=postgresql://postgres:postgres@db:5432/library
EXPOSE 50051 8081
# Use wait-for-db.sh to ensure DB is ready before starting
RUN chmod +x ./wait-for-db.sh && sed -i 's/\r$//' ./wait-for-db.sh
CMD ["./wait-for-db.sh", "python", "app.py"]
