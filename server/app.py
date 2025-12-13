#!/usr/bin/env python3
"""Python gRPC server for Neighborhood Library Service with connection pooling and HTTP health endpoint.

- Uses psycopg2.pool.SimpleConnectionPool for DB connections.
- Starts a small Flask app in a background thread to serve /health HTTP endpoint for Docker healthchecks.
- Each RPC method obtains a connection from the pool, uses it, and returns it.
"""
import os
import time
from concurrent import futures
import grpc
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
from google.protobuf.timestamp_pb2 import Timestamp
from threading import Thread
from flask import Flask, jsonify

try:
    import library_pb2
    import library_pb2_grpc
except Exception:
    raise ImportError("Run server/generate_protos.sh to generate library_pb2.py and library_pb2_grpc.py from protos/library.proto")

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/library')
DB_MINCONN = int(os.environ.get('DB_MINCONN', '1'))
DB_MAXCONN = int(os.environ.get('DB_MAXCONN', '5'))

# Simple Flask health app
health_app = Flask(__name__)

@health_app.route('/health')
def health():
    # basic health: check pool and optionally a lightweight DB check
    try:
        if pool_instance is None:
            return jsonify({'status':'down', 'reason':'no-pool'}), 500
        conn = pool_instance.getconn()
        try:
            cur = conn.cursor()
            cur.execute('SELECT 1')
            cur.fetchone()
        finally:
            pool_instance.putconn(conn)
        return jsonify({'status':'ok'})
    except Exception as e:
        return jsonify({'status':'down', 'reason': str(e)}), 500

pool_instance = None

class LibraryServicer(library_pb2_grpc.LibraryServiceServicer):
    """Implements the LibraryService using a connection pool."""
    def __init__(self, pool):
        self.pool = pool

    def _get_conn(self):
        return self.pool.getconn()

    def _put_conn(self, conn):
        self.pool.putconn(conn)

    def _row_to_book(self, row):
        b = library_pb2.Book(
            id=row['id'],
            isbn=row.get('isbn') or '',
            title=row['title'],
            author=row.get('author') or '',
            publisher=row.get('publisher') or ''
        )
        if row.get('published_date'):
            ts = Timestamp(); ts.FromDatetime(row['published_date']); b.published_date.CopyFrom(ts)
        return b

    def _row_to_member(self, row):
        return library_pb2.Member(id=row['id'], name=row['name'], email=row.get('email') or '', phone=row.get('phone') or '', address=row.get('address') or '')

    def _row_to_borrowing(self, row):
        bor = library_pb2.Borrowing(id=row['id'], book_id=row['book_id'], member_id=row['member_id'], status=row['status'])
        if row.get('borrowed_at'):
            ts = Timestamp(); ts.FromDatetime(row['borrowed_at']); bor.borrowed_at.CopyFrom(ts)
        if row.get('due_at'):
            ts = Timestamp(); ts.FromDatetime(row['due_at']); bor.due_at.CopyFrom(ts)
        if row.get('returned_at'):
            ts = Timestamp(); ts.FromDatetime(row['returned_at']); bor.returned_at.CopyFrom(ts)
        return bor

    def CreateBook(self, request, context):
        """Insert a new book and return it."""
        b = request.book
        conn = self._get_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("INSERT INTO books(isbn, title, author, publisher, published_date, created_at, updated_at) VALUES (%s,%s,%s,%s,%s, now(), now()) RETURNING *",
                            (b.isbn or None, b.title, b.author or None, b.publisher or None, b.published_date.ToDatetime() if b.HasField('published_date') else None))
                row = cur.fetchone()
                conn.commit()
                return library_pb2.CreateBookResponse(book=self._row_to_book(row))
        finally:
            self._put_conn(conn)

    def UpdateBook(self, request, context):
        """Update an existing book identified by id."""
        b = request.book
        conn = self._get_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("UPDATE books SET isbn=%s, title=%s, author=%s, publisher=%s, published_date=%s, updated_at=now() WHERE id=%s RETURNING *",
                            (b.isbn or None, b.title, b.author or None, b.publisher or None, b.published_date.ToDatetime() if b.HasField('published_date') else None, b.id))
                row = cur.fetchone()
                if not row:
                    context.set_code(grpc.StatusCode.NOT_FOUND); context.set_details('Book not found'); return library_pb2.UpdateBookResponse()
                conn.commit()
                return library_pb2.UpdateBookResponse(book=self._row_to_book(row))
        finally:
            self._put_conn(conn)

    def CreateMember(self, request, context):
        """Insert a new member and return it."""
        m = request.member
        conn = self._get_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("INSERT INTO members(name,email,phone,address,created_at,updated_at) VALUES (%s,%s,%s,%s,now(),now()) RETURNING *",
                            (m.name, m.email or None, m.phone or None, m.address or None))
                row = cur.fetchone(); conn.commit(); return library_pb2.CreateMemberResponse(member=self._row_to_member(row))
        finally:
            self._put_conn(conn)

    def UpdateMember(self, request, context):
        """Update a member record."""
        m = request.member
        conn = self._get_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("UPDATE members SET name=%s,email=%s,phone=%s,address=%s,updated_at=now() WHERE id=%s RETURNING *",
                            (m.name, m.email or None, m.phone or None, m.address or None, m.id))
                row = cur.fetchone()
                if not row:
                    context.set_code(grpc.StatusCode.NOT_FOUND); context.set_details('Member not found'); return library_pb2.UpdateMemberResponse()
                conn.commit(); return library_pb2.UpdateMemberResponse(member=self._row_to_member(row))
        finally:
            self._put_conn(conn)

    def BorrowBook(self, request, context):
        """Create a borrowing record after validating book & member and ensuring no active borrow."""
        conn = self._get_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute('SELECT id FROM books WHERE id=%s', (request.book_id,))
                book = cur.fetchone()
                if not book:
                    context.set_code(grpc.StatusCode.NOT_FOUND); context.set_details('Book not found'); return library_pb2.BorrowBookResponse()
                cur.execute('SELECT id FROM members WHERE id=%s', (request.member_id,))
                member = cur.fetchone()
                if not member:
                    context.set_code(grpc.StatusCode.NOT_FOUND); context.set_details('Member not found'); return library_pb2.BorrowBookResponse()
                cur.execute("SELECT * FROM borrowings WHERE book_id=%s AND status='BORROWED'", (request.book_id,))
                active = cur.fetchone()
                if active:
                    context.set_code(grpc.StatusCode.FAILED_PRECONDITION); context.set_details('Book already borrowed'); return library_pb2.BorrowBookResponse()
                due = request.due_at.ToDatetime() if request.HasField('due_at') else None
                cur.execute('INSERT INTO borrowings(book_id, member_id, borrowed_at, due_at, status) VALUES (%s,%s,now(),%s,%s) RETURNING *', (request.book_id, request.member_id, due, 'BORROWED'))
                row = cur.fetchone(); conn.commit(); return library_pb2.BorrowBookResponse(borrowing=self._row_to_borrowing(row))
        finally:
            self._put_conn(conn)

    def ReturnBook(self, request, context):
        """Mark a borrowing as returned."""
        conn = self._get_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute('SELECT * FROM borrowings WHERE id=%s', (request.borrowing_id,))
                row = cur.fetchone()
                if not row:
                    context.set_code(grpc.StatusCode.NOT_FOUND); context.set_details('Borrowing record not found'); return library_pb2.ReturnBookResponse()
                if row['status'] != 'BORROWED':
                    context.set_code(grpc.StatusCode.FAILED_PRECONDITION); context.set_details('Already returned'); return library_pb2.ReturnBookResponse()
                cur.execute("UPDATE borrowings SET returned_at=now(), status='RETURNED' WHERE id=%s RETURNING *", (request.borrowing_id,))
                updated = cur.fetchone(); conn.commit(); return library_pb2.ReturnBookResponse(borrowing=self._row_to_borrowing(updated))
        finally:
            self._put_conn(conn)

    def ListBorrowedByMember(self, request, context):
        """List active borrowings for a member."""
        conn = self._get_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM borrowings WHERE member_id=%s AND status='BORROWED'", (request.member_id,))
                rows = cur.fetchall(); borrows = [self._row_to_borrowing(r) for r in rows]; return library_pb2.ListBorrowedByMemberResponse(borrowings=borrows)
        finally:
            self._put_conn(conn)

    def ListMembers(self, request, context):
        """Return all members (no pagination)."""
        conn = self._get_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute('SELECT * FROM members ORDER BY id')
                rows = cur.fetchall()
                members = [self._row_to_member(r) for r in rows]
                return library_pb2.ListMembersResponse(members=members)
        finally:
            self._put_conn(conn)

    def ListBooks(self, request, context):
        """Return all books (no pagination)."""
        conn = self._get_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute('SELECT * FROM books ORDER BY id')
                rows = cur.fetchall(); books = [self._row_to_book(r) for r in rows]; return library_pb2.ListBooksResponse(books=books)
        finally:
            self._put_conn(conn)

def start_health_server():
    # Run Flask health app on port 8081
    health_app.run(host='0.0.0.0', port=8081)

def serve():
    global pool_instance
    # Initialize connection pool
    # DATABASE_URL expected in form postgresql://user:pass@host:port/db
    dsn = DATABASE_URL
    # psycopg2 pool expects separate params; using simple connection string is fine for connect
    pool_instance = psycopg2.pool.SimpleConnectionPool(DB_MINCONN, DB_MAXCONN, dsn)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    library_pb2_grpc.add_LibraryServiceServicer_to_server(LibraryServicer(pool_instance), server)
    port = os.environ.get('GRPC_PORT', '50051')
    server.add_insecure_port(f'[::]:{port}')

    # Start health HTTP server in background thread
    t = Thread(target=start_health_server, daemon=True)
    t.start()

    server.start()
    print(f'gRPC server started on {port} with HTTP health on 8081')
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()
