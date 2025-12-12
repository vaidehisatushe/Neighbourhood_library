const PROTO_PATH = __dirname + '/../protos/library.proto';
const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');
const packageDefinition = protoLoader.loadSync(PROTO_PATH, {keepCase: true, longs: String, enums: String, defaults: true, oneofs: true});
const proto = grpc.loadPackageDefinition(packageDefinition).library;
const GRPC_ADDR = process.env.GRPC_ADDR || 'server:50051';
const client = new proto.LibraryService(GRPC_ADDR, grpc.credentials.createInsecure());
module.exports = { client, grpc };