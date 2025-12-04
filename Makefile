# Makefile for common development tasks

.PHONY: all build up down logs test proto-client proto-server frontend gateway clean

all: build up

build:
	docker compose build --progress=plain

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs --tail=100 --timestamps

test:
	docker compose exec server pytest -q

proto-client:
	python -m grpc_tools.protoc -Iprotos --python_out=clients --grpc_python_out=clients protos/library.proto

proto-server:
	python -m grpc_tools.protoc -Iprotos --python_out=server --grpc_python_out=server protos/library.proto

frontend:
	cd frontend && npm install && npm run dev

gateway:
	cd gateway && npm install && node server.js

clean:
	docker compose down -v --remove-orphans
	rm -rf server/__pycache__ clients/__pycache__ server/*.pyc clients/*.pyc
