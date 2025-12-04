#!/bin/sh
# wait-for-db.sh - wait until Postgres is accepting connections
set -e
host=${DB_HOST:-db}
port=${DB_PORT:-5432}
user=${DB_USER:-postgres}
until pg_isready -h "$host" -p "$port" -U "$user"; do
  echo "Waiting for postgres at $host:$port..."
  sleep 1
done
echo "Postgres is ready"
exec "$@"
