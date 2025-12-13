const express = require('express');
const bodyParser = require('body-parser');
const { client, grpc } = require('./api_client');
const app = express();
const cors = require('cors');
app.use(cors());
app.use(bodyParser.json());

// Books
app.get('/books', (req, res) => client.ListBooks({}, (err, response) => err ? res.status(500).json(err) : res.json(response.books)));
app.post('/books', (req, res) => client.CreateBook({ book: req.body }, (err, response) => {
  if (err) {
    const status = (err.code === grpc.status.ALREADY_EXISTS) ? 409 : 500;
    return res.status(status).json({ error: err.details || err.message });
  }
  res.json(response.book);
}));
app.put('/books/:id', (req, res) => {
  const id = Number(req.params.id);
  const book = req.body || {};
  client.UpdateBook({ book: { id: id, title: book.title || '', author: book.author || '', isbn: book.isbn || '', publisher: book.publisher || '' } }, (err, response) => {
    if (err) {
      const status = (err.code === grpc.status.NOT_FOUND) ? 404 : (err.code === grpc.status.ALREADY_EXISTS ? 409 : 400);
      return res.status(status).json({ error: err.details || err.message });
    }
    res.json(response.book);
  });
});
app.delete('/books/:id', (req, res) => {
  const id = Number(req.params.id);
  client.DeleteBook({ book_id: id }, (err, response) => {
    if (err) {
      const status = (err.code === grpc.status.NOT_FOUND) ? 404 : (err.code === grpc.status.FAILED_PRECONDITION ? 409 : 500);
      res.status(status).json({ error: err.details || err.message });
    } else {
      res.json(response);
    }
  });
});

// Members
app.get('/members', (req, res) => client.ListMembers({}, (err, response) => err ? res.status(500).json(err) : res.json(response.members)));
app.get('/members/:id', (req, res) => client.GetMember({ id: Number(req.params.id) }, (err, response) => err ? res.status(500).json(err) : res.json(response.member)));
app.post('/members', (req, res) => client.CreateMember({ member: req.body }, (err, response) => {
  if (err) {
    const status = (err.code === grpc.status.ALREADY_EXISTS) ? 409 : 500;
    return res.status(status).json({ error: err.details || err.message });
  }
  res.json(response.member);
}));

app.put('/members/:id', (req, res) => {
  const id = Number(req.params.id);
  const member = req.body || {};
  client.UpdateMember({ member: { id: id, name: member.name || '', email: member.email || '', phone: member.phone || '', address: member.address || '' } }, (err, response) => {
    if (err) {
      const status = (err.code === grpc.status.NOT_FOUND) ? 404 : (err.code === grpc.status.ALREADY_EXISTS ? 409 : 400);
      return res.status(status).json({ error: err.details || err.message });
    }
    res.json(response.member);
  });
});
app.delete('/members/:id', (req, res) => {
  const id = Number(req.params.id);
  client.DeleteMember({ member_id: id }, (err, response) => {
    if (err) {
      const status = (err.code === grpc.status.NOT_FOUND) ? 404 : (err.code === grpc.status.FAILED_PRECONDITION ? 409 : 500);
      res.status(status).json({ error: err.details || err.message });
    } else {
      res.json(response);
    }
  });
});
app.get('/members/:id/borrowed', (req, res) => {
  client.ListBorrowedByMember({ member_id: Number(req.params.id) }, (err, response) => err ? res.status(500).json(err) : res.json(response.borrowings));
});

// Borrow/Return
app.post('/borrow', (req, res) => {
  const b = req.body;
  client.BorrowBook({ book_id: b.book_id, member_id: b.member_id }, (err, response) => {
    if (err) return res.status(400).json({ error: err.details || err.message });
    res.json(response.borrowing);
  });
});
app.post('/return', (req, res) => {
  client.ReturnBook({ borrowing_id: req.body.borrowing_id }, (err, response) => err ? res.status(400).json({ error: err.details }) : res.json(response.borrowing));
});

app.listen(8080, () => console.log('Gateway listening on 8080'));
