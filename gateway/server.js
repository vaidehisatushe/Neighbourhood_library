// Node.js Gateway: exposes simple REST endpoints that call the gRPC server.
// Each route includes a comment explaining its purpose.
const PROTO_PATH = __dirname + '/../protos/library.proto';
const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');
const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');

const packageDefinition = protoLoader.loadSync(PROTO_PATH, {keepCase: true, longs: String, enums: String, defaults: true, oneofs: true});
const proto = grpc.loadPackageDefinition(packageDefinition).library;

// Connect to gRPC server (use service name 'server' in Docker Compose network)
const client = new proto.LibraryService('server:50051', grpc.credentials.createInsecure());
const app = express();
// Enable CORS for the frontend (only allow localhost:3000)
app.use(cors({ origin: 'http://localhost:3000' }));
app.use(bodyParser.json());

// Helper to map gRPC errors to HTTP responses
function handleGrpcError(res, err) {
  if (!err) return false
  const message = err.details || err.message || 'gRPC error'
  switch (err.code) {
    case grpc.status.NOT_FOUND:
      return res.status(404).json({ error: message })
    case grpc.status.INVALID_ARGUMENT:
      return res.status(400).json({ error: message })
    case grpc.status.FAILED_PRECONDITION:
      return res.status(409).json({ error: message })
    default:
      return res.status(500).json({ error: message })
  }
}

// GET /books -> call ListBooks RPC to fetch all books
app.get('/books', (req, res) => {
  client.ListBooks({}, (err, response) => {
    if (err) return handleGrpcError(res, err);
    res.json(response.books || []);
  });
});

// POST /books -> call CreateBook RPC to create a book record
app.post('/books', (req, res) => {
  client.CreateBook({ book: req.body }, (err, response) => {
    if (err) return handleGrpcError(res, err);
    res.json(response.book || {});
  });
});

// POST /borrow -> call BorrowBook RPC to borrow a book
app.post('/borrow', (req, res) => {
  const body = req.body; // expects { book_id, member_id, due_at (optional ISO string) }
  // Note: this gateway sends only numeric ids and ignores due_at for brevity.
  // Basic validation
  if (!body || !body.book_id || !body.member_id) return res.status(400).json({ error: 'book_id and member_id are required' })
  client.BorrowBook({ book_id: body.book_id, member_id: body.member_id }, (err, response) => {
    if (err) return handleGrpcError(res, err);
    res.json(response.borrowing || {});
  });
});

// POST /return -> call ReturnBook RPC to return a borrowed book
app.post('/return', (req, res) => {
  if (!req.body || !req.body.borrowing_id) return res.status(400).json({ error: 'borrowing_id is required' })
  client.ReturnBook({ borrowing_id: req.body.borrowing_id }, (err, response) => {
    if (err) return handleGrpcError(res, err);
    res.json(response.borrowing || {});
  });
});

// GET /member/:id/borrowed -> list currently borrowed books for a member
app.get('/member/:id/borrowed', (req, res) => {
  client.ListBorrowedByMember({ member_id: Number(req.params.id) }, (err, response) => {
    if (err) return handleGrpcError(res, err);
    res.json(response.borrowings || []);
  });
});

app.listen(8080, () => console.log('Gateway listening on 8080'));


// Members endpoints
app.get('/members', (req, res) => {
  if (!client.ListMembers) return res.status(501).json({ error: 'ListMembers not implemented in gRPC' })
  client.ListMembers({}, (err, response) => {
    if (err) return handleGrpcError(res, err)
    res.json(response.members || [])
  })
})

app.post('/members', (req, res) => {
  if (!req.body || !req.body.name) return res.status(400).json({ error: 'member.name is required' })
  client.CreateMember({ member: req.body }, (err, response) => {
    if (err) return handleGrpcError(res, err)
    res.json(response.member || {})
  })
})
