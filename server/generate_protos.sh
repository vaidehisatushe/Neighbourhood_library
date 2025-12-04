#!/bin/bash
# Generate python protobuf and grpc code from protos/library.proto
python -m grpc_tools.protoc -I../protos --python_out=. --grpc_python_out=. ../protos/library.proto
