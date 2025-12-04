import unittest
from unittest.mock import MagicMock, patch
import library_pb2
from library_pb2 import Book

# We import the servicer class dynamically
from server.app import LibraryServicer

class FakeCursor:
    def __init__(self, rows=None):
        self._rows = rows or []
    def execute(self, *args, **kwargs):
        pass
    def fetchone(self):
        return self._rows.pop(0) if self._rows else None
    def fetchall(self):
        return self._rows
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        pass

class FakeConn:
    def __init__(self, rows=None):
        self._rows = rows or []
        self.cursor_obj = FakeCursor(self._rows)
    def cursor(self, cursor_factory=None):
        return self.cursor_obj
    def commit(self):
        pass

class ServicerTests(unittest.TestCase):
    def setUp(self):
        # Create a fake pool that returns our fake connection
        fake_pool = MagicMock()
        fake_conn = FakeConn([{'id':1, 'title':'T', 'isbn':'123', 'author':'A', 'publisher':'P', 'published_date':None}])
        fake_pool.getconn.return_value = fake_conn
        fake_pool.putconn.return_value = None
        self.servicer = LibraryServicer(fake_pool)

    def test_create_book(self):
        req = library_pb2.CreateBookRequest(book=library_pb2.Book(title='T', author='A'))
        # Should not throw
        resp = self.servicer.CreateBook(req, None)
        self.assertIsNotNone(resp.book)

if __name__ == '__main__':
    unittest.main()
